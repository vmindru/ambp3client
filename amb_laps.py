#!/usr/bin/env python
from time import sleep
from sys import exit
from os import system as sys_command

from amb_client import open_mysql_connection
from amb_client import get_args


def main():
    config = get_args()
    conf = config.conf
    mysql_enabled = conf['mysql_backend']
    if mysql_enabled:
        mysql_con = open_mysql_connection(user=conf['mysql_user'],
                                          db=conf['mysql_db'],
                                          password=conf['mysql_password']
                                          )
        my_cursor = mysql_con.cursor()
    try:
        if mysql_enabled:
            while True:
                sleep(0.5)
                my_cursor.execute('select * from passes limit 10')
                for result in my_cursor.fetchall():
                    print(result)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)


if __name__ == "__main__":
    main()
