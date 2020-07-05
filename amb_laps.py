#!/usr/bin/env python
from mysql.connector import Error as MysqlError
from time import sleep
import logging

from amb_client import open_mysql_connection
from amb_client import get_args
from AmbP3.time_server import DecoderTime
from AmbP3.time_client import TimeClient
from AmbP3.time_server import TIME_IP
from AmbP3.time_server import TIME_PORT

# PASSES = [ "db_entry_id", "pass_id", "transponder_id", "rtc_time", "strength", "hits", "flags", "decoder_id" ]
DEFAULT_HEAT_DURATION = 590
DEFAULT_HEAT_COOLDOWN = 90
DEAFULT_HEAT_INTERVAL = 90
DEFAULT_MINIMUM_LAP_TIME = 10
DEFAULT_HEAT_SETTINGS = ["heat_duration", "heat_cooldown"]
MAX_GET_TIME_ATTEMPTS = 30


def IsInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def list_to_dict(mylist, index=0):
    "convert a list, tuple into dict by index key"
    foo = {}
    for item in mylist:
        key = item[index]
        values = list(item)
        del values[index]
        foo[key] = values
    return foo


def mysql_connect(conf):
    try:
        con = open_mysql_connection(user=conf['mysql_user'],
                                    db=conf['mysql_db'],
                                    password=conf['mysql_password'],
                                    host=conf['mysql_host'],
                                    port=conf['mysql_port'],)
    except MysqlError as err:
        logging.error("Something went wrong: {}".format(err))
    if con is None:
        logging.error("Failed to open DB connection, exiting")
        exit(1)
    else:
        return con
    con.autocommit = True


def sql_write(mycon, query):
    mysql = mycon[0]
    cursor = mycon[1]
    cursor.execute(query)
    mysql.commit()
    logging.debug("insert query: {}, results: {}".format(query, cursor.rowcount))
    return(cursor.rowcount)


def sql_select(cursor, query):
    cursor.execute(query)
    results = cursor.fetchall()
    logging.debug("select query: {}, results: {}".format(query, cursor.rowcount))
    return results


class Pass():
    def __init__(self, db_entry_id, pass_id, transponder_id, rtc_time, strength, hits, flags, decoder_id):
        self.db_entry_id = db_entry_id
        self.pass_id = pass_id
        self.transponder_id = transponder_id
        self.rtc_time = rtc_time
        self.strength = strength
        self.hits = hits
        self.flags = flags
        self.decoder_id = decoder_id


class Heat():
    def __init__(self, conf, decoder_time, heat_duration=DEFAULT_HEAT_DURATION, heat_cooldown=DEFAULT_HEAT_COOLDOWN,
                 minimum_lap_time=DEFAULT_MINIMUM_LAP_TIME, race_flag=0):
        self.conf = conf
        self.dt = decoder_time
        self.mysql = mysql_connect(conf)
        self.heat_duration = heat_duration
        self.heat_cooldown = heat_cooldown
        self.race_flag = race_flag
        self.minimum_lap_time = minimum_lap_time
        self.cursor = self.mysql.cursor()
        self.mycon = (self.mysql, self.cursor)
        " GET HEAT SETTINGS BEFORE POTENTIALLY CREATING NEW HEAT,"
        query = "select * from settings"
        results = list(sql_select(self.cursor, query))
        if len(results) > 0:
            for result in results:
                setting = result[0]
                setting_value = result[1]
                setting_value = int(setting_value) if IsInt(setting_value) else setting_value
                logging.debug("Found {}: {}".format(setting, setting_value))
                setattr(self, setting, setting_value)
        self.heat = self.get_heat()
        self.heat_id = self.heat[0]
        self.heat_finished = self.heat[1]
        self.first_pass_id = self.heat[2]
        self.last_pass_id = self.heat[3]
        self.rtc_time_start = self.heat[4]
        self.rtc_time_end = self.heat[5]
        self.race_flag = self.heat[6]
        self.rtc_max_duration = self.heat[7]
        if bool(self.first_pass_id) is True:
            self.first_transponder = self.get_transponder(self.first_pass_id)

    def get_heat(self):
        """ get's current running heat, if no heat is running will create one """
        query = "select * from heats where heat_finished=0 order by heat_id desc limit 1"
        result = sql_select(self.cursor, query)
        result_len = len(list(result))
        if result_len > 0:
            heat = result[0]
            logging.debug("Found running heat {}".format(heat))
            return heat
        else:
            self.first_pass_id, self.rtc_time_start, self.rtc_time_end = self.create_heat()
            return self.get_heat()

    def is_running(self, heat_id):
        query = f"select heat_finished from heats where heat_id = {heat_id}"
        result = sql_select(self.cursor, query)
        result_len = len(list(result))
        if result_len > 0:
            heat_finished = result[0][0]
        if bool(self.heat_finished) or bool(heat_finished):
            logging.debug("HEAT FINISHED")
            return False
        else:
            return True

    def get_pass_timestamp(self, pass_id):
        return sql_select(self.cursor, "select rtc_time from passes where pass_id={}".format(pass_id))[0][0]

    def get_transponder(self, pass_id):
        query = "select transponder_id from passes where pass_id={}".format(pass_id)
        result = sql_select(self.cursor, query)[0][0]
        transponder_id = result
        return transponder_id

    def process_heat_passes(self):
        "process heat_passes"
        if bool(self.first_pass_id):
            sleep(0.5)
            self.rtc_max_duration = self.rtc_time_start + ((self.heat_duration + self.heat_cooldown) * 1000000)
            self.first_transponder = self.get_transponder(self.first_pass_id)
            """ FIX ME heat_not_processed_passes_query MUST BE MORE SIMPLE """
            all_heat_passes_query = f"""select * from passes where pass_id >= {self.first_pass_id} and rtc_time <=
{self.rtc_max_duration} union all ( select * from passes where rtc_time > {self.rtc_max_duration} limit 1 )"""
            heat_not_processed_passes_query = f"""select passes.* from ( {all_heat_passes_query} ) as passes left join laps on
passes.pass_id = laps.pass_id where laps.heat_id is NULL"""
            #  print(heat_not_processed_passes_query)
            not_processed_passes = sql_select(self.cursor, heat_not_processed_passes_query)
            for pas in not_processed_passes:
                pas = Pass(*pas)
                if pas.rtc_time > self.rtc_max_duration:
                    self.finish_heat()
                    break
                else:
                    self.add_pass_to_laps(self.heat_id, pas)
                    if not self.finish_heat and pas.rtc_time > self.rtc_time_end:
                        self.wave_finish_flag()

    def finish_heat(self):
        query = f"select pass_id from laps where heat_id={self.heat_id} order by pass_id desc limit 1"
        result = sql_select(self.cursor, query)
        pass_id = result[0][0] if len(result) > 0 else "NULL"
        logging.debug(f"finish heat_id {self.heat_id}, with pass_id: {pass_id}")
        query = "update heats set heat_finished=1, last_pass_id={} where heat_id = {}".format(pass_id, self.heat_id)
        sql_write(self.mycon, query)
        self.heat_finished = 1
        self.heat_flag = 2

    def valid_lap_time(self, pas):
        self.previous_lap_times = {}
        previous_lap_query = f"""select rtc_time from laps where heat_id={self.heat_id}
 and transponder_id={pas.transponder_id} and pass_id<{pas.pass_id} order by pass_id desc limit 1"""

        if pas.transponder_id not in self.previous_lap_times:
            qresult = sql_select(self.cursor, previous_lap_query)
            if len(qresult) > 0:
                self.previous_lap_times[pas.transponder_id] = qresult[0][0]
            else:
                self.previous_lap_times[pas.transponder_id] = 0

        if pas.rtc_time - self.previous_lap_times[pas.transponder_id] > self.minimum_lap_time * 1000000:
            return True
        else:
            query = f"delete from passes where pass_id = {pas.pass_id}"
            sql_write(self.mycon, query)
            return False

    def wave_finish_flag(self):
        query = f"update  heats set finish_flag = 1 where heat_id={self.heat_id}"
        sql_write(self.mycon, query)
        self.race_flag = 1

    def add_pass_to_laps(self, heat_id, pas):
        lap = {"heat_id": heat_id,
               "pass_id": pas.pass_id,
               "transponder_id": pas.transponder_id,
               "rtc_time": pas.rtc_time}
        keys = ", ".join(lap.keys())
        values = tuple(lap.values())
        if self.valid_lap_time(pas):
            query = "insert into laps ({}) values {}".format(keys, values)
            sql_write(self.mycon, query)
        else:
            pass

    def create_heat(self):
        """ waits for a new pass and creates a new HEAT
        Parameters:
        mycon: mysql connection and cursor tuple
        heat_duration: create heat with heat_duration

        Returns:
        pass_id: pass id
        rtc_time_start: heat start time
        rtc_time_end: heat end time
        """
        SLEEP_TIME = 1
        cursor = self.mycon[1]

        while True:
            query = "select value from settings where setting = 'green_flag'"
            result = list(sql_select(cursor, query))
            result = result[0][0]
            if len(result) > 0 and bool(int(result)):
                green_flag_time = self.get_decoder_time()
                logging.debug(f"Green Flag is: {result}! Race can start  after: {green_flag_time}")
                break
            else:
                logging.debug("Waiting for Green Flag")
            sleep(SLEEP_TIME)

        while True:
            query = f"""select * from passes where pass_id > ( select pass_id from laps order by pass_id desc limit 1 )
and rtc_time > {green_flag_time} limit 1"""
            result = sql_select(cursor, query)

            if not len(result) > 0:
                sleep(SLEEP_TIME)
                logging.debug("Waiting on new Pass")
                continue
            else:
                starting_pass = Pass(*result[0])
                self.first_pass_id = starting_pass.pass_id
                self.rtc_time_start = starting_pass.rtc_time
                self.rtc_time_end = self.rtc_time_start + (self.heat_duration * 1000000)
                self.rtc_max_duration = self.rtc_time_start + ((self.heat_duration + self.heat_cooldown) * 1000000)
                logging.debug("last pass at {}".format(self.rtc_time_start))
                columns = "first_pass_id, rtc_time_start, rtc_time_end, rtc_time_max_end"
                values = f"{self.first_pass_id}, {self.rtc_time_start}, {self.rtc_time_end}, {self.rtc_max_duration}"
                logging.debug(f"creating new heat starting starting_pass: {starting_pass.pass_id}, heat_duration: {self.heat_duration}")
                insert_query = f"insert into heats ({columns}) values ({values})"
                print(insert_query)
                if sql_write(self.mycon, insert_query) > 0:
                    return starting_pass.pass_id, self.rtc_time_start, self.rtc_time_end

    def check_if_all_finished(self):
        query_number_of_racers = f"select count(distinct transponder_id) from laps where heat_id={self.heat_id}"
        query_number_of_racers_finished = f"""select count(transponder_id) from laps where heat_id={self.heat_id}
 and rtc_time > {self.heat_rtc_finish}"""
        number_of_racers_in_race = sql_select(self.cursor, query_number_of_racers)
        number_of_racers_finished = sql_select(self.cursor, query_number_of_racers_finished)
        if len(number_of_racers_in_race) > 0 and number_of_racers_finished > 0 and number_of_racers_finished >= number_of_racers_in_race:
            return True
        else:
            return False

    def run_heat(self):
        logging.debug("RUNNING HEAT")
        current_transponder_time = self.get_decoder_time()
        while self.is_running(self.heat_id):
            if self.race_flag > 0:
                """ if race flag is 1 or 2 non-green, check if we are still racing and exit """
                """ wait for MAX time and the finish teh race """
                if self.race_flag == 2:
                    logging.debug(" #0#0#0#0#0#0 FIRST The race is over, exiting #0#0#0#0#0#0#0#0#)")
                    break

                if self.check_if_all_finished():
                    logging.debug(" #0#0#0#0#0#0 EVERY ONE FINSIHED The race is over, exiting #0#0#0#0#0#0#0#0#)")
                    self.finish_heat()
                    break

                if self.get_decoder_time() > self.rtc_max_duration:
                    logging.debug(" #0#0#0#0#0#0 The race is over, exiting #0#0#0#0#0#0#0#0#)")
                    self.finish_heat()
                    break

            if current_transponder_time > self.rtc_max_duration:
                logging.debug(" #0#0#0#0#0#0 Finish the heat  #0#0#0#0#0#0#0#0#)")
                self.finish_heat()
            else:
                logging.debug(" #0#0#0#0#0#0 processing_passes #0#0#0#0#0#0#0#0#)")
                self.process_heat_passes()

    def get_decoder_time(self):
        while not self.dt.decoder_time:
            sleep(1)
            logging.error("Waiting on time")
        else:
            print(f"################### {self.dt.decoder_time} #####################################")
            return self.dt.decoder_time

    def get_kart_id(self, transponder_id):
        """ converts transpodner name to  kart number and kart name """
        query = "select name, kart_number from karts where transponder_id = {}".format(transponder_id)
        result = sql_select(self.mycon, query)
        if len(result) == 1:
            return result[0]
        else:
            return transponder_id


def main():
    """ IMPLEMENT CONNECT TO CLIENT PYTHON AND GET TIME ALL THE TIME """
    config = get_args()
    conf = config.conf
    logging.basicConfig(level=logging.DEBUG)
    dt = DecoderTime(0)
    TimeClient(dt, TIME_IP, TIME_PORT)
    while True:
        heat = Heat(conf, decoder_time=dt)
        heat.run_heat()


if __name__ == "__main__":
    main()
