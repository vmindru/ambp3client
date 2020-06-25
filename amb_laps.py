#!/usr/bin/env python
import logging

from time import sleep

from amb_client import open_mysql_connection
from amb_client import get_args
# from pprint import pprint


# PASSES = [ "db_entry_id", "pass_id", "transponder_id", "rtc_time", "strength", "hits", "flags", "decoder_id" ]
DEFAULT_HEAT_DURATION = 590
DEFAULT_HEAT_COOLDOWN = 90
DEAFULT_HEAT_INTERVAL = 90
DEFAULT_MINIMUM_LAP_TIME = 10
DEFAULT_HEAT_SETTINGS = ["heat_duration", "heat_cooldown"]


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
    con = open_mysql_connection(user=conf['mysql_user'],
                                db=conf['mysql_db'],
                                password=conf['mysql_password'],
                                host=conf['mysql_host'],
                                port=conf['mysql_port'],)
    con.autocommit = True
    if con is None:
        print("Failed to open DB connection, exiting")
        exit(1)  # THIS IS VERY DIRTY NEEDS FIX
    else:
        return con


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


def init_db(mysql, heat_duration=DEFAULT_HEAT_DURATION):
    cursor = mysql.cursor()
    query = "select 1 from heats limit 1"
    sql_select(cursor, query)
    if not cursor.rowcount > 0:
        Heat.create_heat((mysql, cursor), heat_duration=DEFAULT_HEAT_DURATION, new=True)
        exit(0)


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
    def __init__(self, mysql, heat_duration=DEFAULT_HEAT_DURATION, heat_cooldown=DEFAULT_HEAT_COOLDOWN,
                 minimum_lap_time=DEFAULT_MINIMUM_LAP_TIME, finish_flauge=False):
        self.heat_duration = heat_duration
        self.heat_cooldown = heat_cooldown
        self.finish_flague = False
        self.minimum_lap_time = minimum_lap_time
        self.mysql = mysql
        self.cursor = self.mysql.cursor()
        self.mycon = (self.mysql, self.cursor)
        """ GET HEAT SETTINGS BEFORE POTENTIALLY CREATING NEW HEAT,
        I DON'T LIKE GET_HEAT Creates a heat... need to change this"""
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
            self.first_pass_id, self.rtc_time_start, self.rtc_time_end = Heat.create_heat(self.mycon, self.heat_duration)
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

    def get_pass_rtc(self, pass_id):
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
            self.first_pass_rtc = self.get_pass_rtc(self.first_pass_id)
            self.heat_rtc_finish = self.first_pass_rtc + (self.heat_duration * 1000000)
            self.heat_rtc_max_duration = self.first_pass_rtc + ((self.heat_duration + self.heat_cooldown) * 1000000)
            self.first_transponder = self.get_transponder(self.first_pass_id)
            all_heat_passes_query = "select * from passes where pass_id >= {} and rtc_time <= \
{rtc_max_duration} union all ( select * from passes where rtc_time > {rtc_max_duration} \
limit 1 )".format(self.first_pass_id, rtc_max_duration=self.heat_rtc_max_duration)
            heat_not_processed_passes_query = "select passes.* from ( {} ) as passes left join laps on \
passes.pass_id = laps.pass_id where laps.heat_id is NULL".format(all_heat_passes_query)
            not_processed_passes = sql_select(self.cursor, heat_not_processed_passes_query)
            for pas in not_processed_passes:
                pas = Pass(*pas)
                if pas.rtc_time > self.heat_rtc_max_duration:
                    query = "select * from passes where pass_id < {} order by pass_id desc limit 1".format(pas.pass_id)
                    last_pass = Pass(*sql_select(self.cursor, query)[0])
                    self.finish_heat(self.heat_id, last_pass.pass_id)
                    break
                else:
                    self.add_pass_to_laps(self.heat_id, pas)

    def finish_heat(self, heat_id, pass_id):
        logging.debug("finish heat {}".format(heat_id))
        query = "update heats set heat_finished=1, last_pass_id={} where heat_id = {}".format(pass_id, heat_id)
        sql_write(self.mycon, query)
        self.heat_finished = True

    def valid_lap_time(self, pas):
        check_if_last_lap_query = f"select pass_id from laps where rtc_time > {self.heat_rtc_finish}\
                                    and rtc_time < {self.heat_rtc_max_duration}"
        query = "select rtc_time from laps where heat_id={} and transponder_id={} order by pass_id desc limit 1".format(self.heat_id,
                                                                                                                        pas.transponder_id)
        previous_rtc_time = sql_select(self.cursor, query)
        in_last_lap = sql_select(self.cursor, check_if_last_lap_query)
        logging.debug(previous_rtc_time)
        if len(previous_rtc_time) < 1 and len(in_last_lap) < 1:
            return True
        elif pas.rtc_time - previous_rtc_time[0][0] > self.minimum_lap_time * 1000000 and len(in_last_lap) < 2:
            return True
        else:
            return False

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

    def create_heat(mycon, heat_duration, new=False):
        """ waits for a new pass and creates a new HEAT
        Parameters:
        mycon: mysql connection and cursor tuple
        heat_duration: create heat with heat_duration

        Returns:
        pass_id: pass id
        rtc_time_start: heat start time
        rtc_time_end: heat max end time
        """
        SLEEP_TIME = 1
        cursor = mycon[1]
        query = "select * from passes order by pass_id desc limit 1"
        result = sql_select(cursor, query)
        last_pass = Pass(*result[0])
        logging.debug("Last entry: {}. Waiting for new one".format(last_pass.pass_id))

        while True:
            query = "select value from settings where setting = 'green_flag'"
            result = list(sql_select(cursor, query))
            result = result[0][0]
            if len(result) > 0 and bool(int(result)):
                logging.debug(f"Green Flag! Race can start value {result}")
                break
            else:
                logging.debug("Waiting for Green Flag")
            sleep(SLEEP_TIME)

        while True:
            query = "select * from passes where pass_id > {} order by pass_id limit 1".format(last_pass.pass_id)
            result = sql_select(cursor, query)

            if not len(result) > 0:
                sleep(SLEEP_TIME)
                logging.debug("Waiting on new Pass")
                continue
            else:
                starting_pass = Pass(*result[0])

            if starting_pass.pass_id > last_pass.pass_id:
                rtc_time_start = starting_pass.rtc_time
                rtc_time_end = rtc_time_start + (heat_duration * 1000000)
                logging.debug("last pass at {}".format(rtc_time_start))
                columns = "first_pass_id, rtc_time_start, rtc_time_end"
                logging.debug("creating new heat starting starting_pass: {}, heat_duration: {}, rtc_time_start: {}, rtc_time_end: {}\
                              ".format(starting_pass.pass_id, heat_duration, rtc_time_start, rtc_time_end))
                insert_query = "insert into heats ({}) values ({},{},{})".format(columns,
                                                                                 starting_pass.pass_id,
                                                                                 rtc_time_start,
                                                                                 rtc_time_end)
                if sql_write(mycon, insert_query) > 0:
                    return starting_pass.pass_id, rtc_time_start, rtc_time_end
            else:
                logging.debug("waiting for new pass")
                sleep(SLEEP_TIME)

    def run_heat(self):
        logging.debug("RUNNING HEAT")
        while self.is_running(self.heat_id):
            self.process_heat_passes()

    def get_kart_id(self, transponder_id):
        """ converts transpodner name to  kart number and kart name """
        query = "select name, kart_number from karts where transponder_id = {}".format(transponder_id)
        result = sql_select(self.mycon, query)
        if len(result) == 1:
            return result[0]
        else:
            return transponder_id


def main():
    config = get_args()
    conf = config.conf
    logging.basicConfig(level=logging.DEBUG)
    init_db(mysql_connect(conf))
    while True:
        mysql = mysql_connect(conf)
        heat = Heat(mysql)
        heat.run_heat()


if __name__ == "__main__":
    main()
