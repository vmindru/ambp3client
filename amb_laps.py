#!/usr/bin/env python
import logging

from time import time
from time import sleep
import json

from amb_client import open_mysql_connection
from amb_client import get_args


def list_to_dict(mylist, index=0):
    "convert a list, tuple into dict by index key"
    foo = {}
    for item in mylist:
        key = item[index]
        values = list(item)
        del values[index]
        foo[key] = values
    return foo


class Heat():
    def __init__(self, conf, heat_duration=590):
        self.started = False
        self.conf = conf
        self.heat_duration = heat_duration
        self.mysql_con = self._mysql_connect()
        self.cursor = self.mysql_con.cursor()
        self.heat = self.get_heat()
        self.heat_id = self.heat[0]
        self.heat_finished = self.heat[1]
        self.karts = json.loads(self.heat[2])
        self.nr_of_laps = self.heat[3]
        self.first_pass_id = self.heat[4]
        self.last_pass_id = self.heat[5]
        self.first_pass_rtc = 0
        if bool(self.first_pass_id) is True:
            self.first_transponder = self.get_transponder(self.first_pass_id)

    def _mysql_connect(self):
        self._db_con_start = time()
        mysql_con = open_mysql_connection(user=self.conf['mysql_user'],
                                          db=self.conf['mysql_db'],
                                          password=self.conf['mysql_password'])
        return mysql_con

    def run_query(self, query):
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return results

    def get_heat(self):
        query = "select * from heats order by heat_id desc limit 1"
        result = self.run_query(query)
        result_len = len(list(result))
        if result_len > 0:
            return result[0]
        else:
            self.create_heat()
            return self.get_heat()

    def is_running(self, heat_id):
        if bool(self.heat_finished) is False:
            return True
        else:
            return False

    def get_heat_passes_not_in_laps(self, first_pass_id, last_pass_id):
        query = "select passes.pass_id,passes.transponder_id,passes.rtc_time from \
( select passes.pass_id,passes.transponder_id,passes.rtc_time from passes where \
pass_id > {} ) as passes \
left join laps on passes.pass_id = laps.pass_id where laps.pass_id is \
NULL".format(first_pass_id, last_pass_id)
        return self.run_query(query)

    def get_pass_rtc(self, pass_id):
        return self.run_query("select rtc_time from passes where pass_id={}".format(self.first_pass_id))[0][0]

    def get_transponder(self, pass_id):
        return self.run_query("select transponder_id from passes where pass_id={}".format(self.first_pass_id))[0][0]

    def process_heat_passes(self):
        "process heat_passes"
        logging.debug("Getting latest passes")
        if bool(self.first_pass_id):
            self.first_pass_rtc = self.get_pass_rtc(self.first_pass_id)
            self.heat_rtc_finish = self.first_pass_rtc + self.heat_duration * 1000000
            self.first_transponder = self.get_transponder(self.first_pass_id)
            query = "select * from passes where"
            query = "{} pass_id >= {} and rtc_time <= {}".format(query, self.first_pass_id, self.heat_rtc_finish)
            passes_query = "select * from ( {} ) as heat_passes left join laps on heat_passes.pass_id = laps.pass_id where \
laps.heat_id is NULL".format(query)
            all_passes_query = "select * from ( {} ) as heat_passes left join laps on heat_passes.pass_id = laps.pass_id \
                               ".format(query)
            get_heat_passes_query = "select * from laps where heat_id = {}".format(self.heat_id)
            not_processed_passes = self.run_query(passes_query)
            processed_heat_passes = self.run_query(get_heat_passes_query)
            self.all_heat_passes = self.run_query(all_passes_query)
            self.not_processed_passes_dict = list_to_dict(not_processed_passes, 1)
            self.heat_passes_dict = list_to_dict(processed_heat_passes, 2)
            for pass_id in self.not_processed_passes_dict:
                if pass_id not in self.heat_passes_dict:
                    self.add_pass_to_laps(pass_id)

    def add_pass_to_laps(self, pass_id):
        transpoder_id = self.not_processed_passes_dict[pass_id][1]
        self.get_kart_id(transpoder_id)

    def create_heat(self):
        logging.debug("creating new heat")
        # result = self.run_query("select * from passes order by db_entry_id desc limit 1")
        # last_pass_id = result[0][0]
        last_pass_id = 10052
        logging.debug("Last entry: {}. Waiting for new one".format(last_pass_id))
        while True:
            query = "select * from passes where db_entry_id > {} order by db_entry_id desc limit 1".format(last_pass_id)
            last_pass = self.run_query(query)[0]
            pass_id = last_pass[0]
            if pass_id > last_pass_id:
                rtc_time_start = last_pass[3]
                rtc_time_end = rtc_time_start + (self.heat_duration * 1000000)
                logging.debug("last pass at {}".format(rtc_time_start))
                columns = "rtc_time_start, rtc_time_end"
                insert = "insert into heats ({}) values ({},{})".format(columns, rtc_time_start, rtc_time_end)
                self.cursor.execute(insert)
                return True
            else:
                logging.debug("waiting for new pass")
                sleep(0.5)

    def run_heat(self):
        "run HEAT with duration"
        self.process_heat_passes()
#        while self.is_running(self.heat_id):
#            self.process_heat_passes()

    def get_kart_id(self, transponder_id):
        """ converts transpodner name to  kart number and kart name """
        query = "select name, kart_number from karts where transponder_id = {}".format(transponder_id)
        result = self.run_query(query)
        if len(result) == 1:
            return result[0]
        else:
            return transponder_id


def main():
    config = get_args()
    conf = config.conf
    logging.basicConfig(level=logging.DEBUG)
    heat = Heat(conf)
    heat.run_heat()
    sleep(0.1)


if __name__ == "__main__":
    main()
