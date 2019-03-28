#!/usr/bin/env python
from time import time

from amb_client import open_mysql_connection
from amb_client import get_args


class heat():
    def __init__(self, conf):
        self.finished = False
        self.started = False
        self.conf = conf
        self.mysql_con = self._mysql_connect()
        self.db_cursor = self.mysql_con.cursor()

    def _mysql_connect(self):
        self._db_con_start = time()
        mysql_con = open_mysql_connection(user=self.conf['mysql_user'],
                                          db=self.conf['mysql_db'],
                                          password=self.conf['mysql_passwor'])
        return mysql_con

    def _get_last_heat(self):
        self.cursor.execute()

    def start():
        pass


def main():
    config = get_args()
    conf = config.conf
    print(conf)


if __name__ == "__main__":
    main()
