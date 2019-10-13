#!/usr/bin/env python
import logging

from time import sleep

from amb_client import open_mysql_connection
from amb_client import get_args
# from pprint import pprint


# PASSES = [ "db_entry_id", "pass_id", "transponder_id", "rtc_time", "strength", "hits", "flags", "decoder_id" ]
DEFAULT_HEAT_DURATION = 590


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
                                password=conf['mysql_password'])
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
    def __init__(self, conf, mysql, heat_duration=590):
        self.conf = conf
        self.heat_duration = heat_duration
        self.mysql = mysql
        self.cursor = self.mysql.cursor()
        self.mycon = (self.mysql, self.cursor)
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
        query = "select * from heats where heat_finished=0 order by heat_id desc limit 1"
        result = sql_select(self.cursor, query)
        result_len = len(list(result))
        if result_len > 0:
            logging.debug("Found running heat {}".format(result[0]))
            heat_id = result[0]
            return heat_id
        else:
            self.first_pass_id, self.rtc_time_start, self.rtc_time_end = Heat.create_heat(self.mycon,
                                                                                          self.heat_duration)
            return self.get_heat()

    def is_running(self, heat_id):
        if bool(self.heat_finished) is False:
            return True
        else:
            return False

    def get_pass_rtc(self, pass_id):
        return sql_select(self.cursor, "select rtc_time from passes where pass_id={}".format(pass_id))[0][0]

    def get_transponder(self, pass_id):
        query = "select transponder_id from passes where pass_id={}".format(pass_id)
        result = sql_select(self.cursor, query)[0][0]
        transpoder_id = result
        return transpoder_id

    def process_heat_passes(self):
        "process heat_passes"
        if bool(self.first_pass_id):
            sleep(0.5)
            self.first_pass_rtc = self.get_pass_rtc(self.first_pass_id)
            self.heat_rtc_finish = self.first_pass_rtc + self.heat_duration * 1000000
            self.first_transponder = self.get_transponder(self.first_pass_id)
            all_heat_passes_query = "select * from passes where pass_id >= {} and rtc_time <= \
{rtc_finish} union all ( select * from passes where rtc_time > {rtc_finish} \
limit 1 )".format(self.first_pass_id, rtc_finish=self.heat_rtc_finish)
            heat_not_processed_passes_query = "select passes.* from ( {} ) as passes left join laps on \
passes.pass_id = laps.pass_id where laps.heat_id is NULL".format(all_heat_passes_query)
            # all_heat_passes = sql_select(self.mycon, all_heat_passes_query)
            not_processed_passes = sql_select(self.cursor, heat_not_processed_passes_query)
            # not_processed_passes = [ {'pass': Pass(*pas)} for pas in not_processed_passes ]
            for pas in not_processed_passes:
                pas = Pass(*pas)
                if pas.rtc_time > self.heat_rtc_finish:
                    query = "select * from passes where pass_id < {} order by pass_id desc limit 1".format(pas.pass_id)
                    last_pass = Pass(*sql_select(self.cursor, query)[0])
                    self.finish_heat(self.heat_id, last_pass.pass_id)
                    break
                else:
                    self.add_pass_to_laps(self.heat_id, pas)

    def finish_heat(self, heat_id, last_pass_id):
        logging.debug("finish heat {}".format(heat_id))
        query = "update heats set heat_finished=1, last_pass_id={} where heat_id = {}".format(last_pass_id, heat_id)
        sql_write(self.mycon, query)
        self.heat_finished = True

    def add_pass_to_laps(self, heat_id, pas):
        lap = {"heat_id": heat_id,
               "pass_id": pas.pass_id,
               "transponder_id": pas.transponder_id,
               "rtc_time": pas.rtc_time}
        keys = ", ".join(lap.keys())
        values = tuple(lap.values())
        query = "insert into laps ({}) values {}".format(keys, values)
        sql_write(self.mycon, query)

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
        cursor = mycon[1]
        logging.debug("creating new heat")
        if new:
            query = "select * from passes order by pass_id asc limit 1"
        else:
            query = "select * from passes where pass_id > ( select last_pass_id  from heats where heat_finished=1 order\
 by heat_id desc limit 1 ) order by db_entry_id asc limit 1"
        result = sql_select(cursor, query)
        last_pass = Pass(*result[0])
        logging.debug("Last entry: {}. Waiting for new one".format(last_pass.pass_id))
        while True:
            query = "select * from passes where pass_id > {} order by pass_id limit 1".format(last_pass.pass_id)
            result = sql_select(cursor, query)
            if not len(result) > 0:
                continue
            else:
                this_pass = Pass(*result[0])
            logging.debug("creating new heat starting this_pass: {}".format(this_pass.pass_id))
            if this_pass.pass_id > last_pass.pass_id:
                rtc_time_start = this_pass.rtc_time
                rtc_time_end = rtc_time_start + (heat_duration * 1000000)
                logging.debug("last pass at {}".format(rtc_time_start))
                columns = "first_pass_id, rtc_time_start, rtc_time_end"
                insert_query = "insert into heats ({}) values ({},{},{})".format(columns,
                                                                                 this_pass.pass_id,
                                                                                 rtc_time_start,
                                                                                 rtc_time_end)
                if sql_write(mycon, insert_query) > 0:
                    return this_pass.pass_id, rtc_time_start, rtc_time_end
            else:
                logging.debug("waiting for new pass")
                sleep(0.5)

    def run_heat(self):
        "run HEAT with duration"
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
        heat = Heat(conf, mysql_connect(conf))
        if not heat.heat_finished:
            heat.run_heat()
        else:
            print(heat.last_pass_id)
        sleep(1)


if __name__ == "__main__":
    main()
