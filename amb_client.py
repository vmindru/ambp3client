#!/usr/bin/env python
from time import sleep
from sys import exit
from argparse import ArgumentParser

import mysql.connector as mysqlconnector

from AmbP3.config import Config
from AmbP3.config import DEFAULT_CONFIG_FILE
from AmbP3.config import DEFAULT_PORT
from AmbP3.config import DEFAULT_IP
from AmbP3.decoder import Connection
from AmbP3.decoder import p3decode as decode
from AmbP3.decoder import bin_data_to_ascii as data_to_ascii
from AmbP3.decoder import bin_dict_to_ascii as dict_to_ascii
from AmbP3.write import Write


def get_args(PORT=DEFAULT_PORT, IP=DEFAULT_IP, config_file=DEFAULT_CONFIG_FILE):
    """ args that overwrite AmbP3.config """
    args = ArgumentParser()
    args.add_argument("-f", "--config", dest='config_file', default=config_file)
    cli_args = args.parse_args()
    config = Config(cli_args.config_file)
    return config


def open_mysql_connection(user, db, password):
    try:
        sql_con = mysqlconnector.connect(user=user, db=db, password=password)
        return sql_con
    except mysqlconnector.errors.ProgrammingError as e:
        print("DB connection failed: {}".format(e))
        return None


def main():
    config = get_args()
    conf = config.conf
    print(conf)
    mysql_enabled = conf['mysql_backend']
    if mysql_enabled:
        mysql_con = open_mysql_connection(user=conf['mysql_user'],
                                          db=conf['mysql_db'],
                                          password=conf['mysql_password']
                                          )
        my_cursor = mysql_con.cursor()
    connection = Connection(config.ip, config.port)
    connection.connect()

    if not config.file:
        print("file not defined in config")
        exit(1)
    elif not config.debug_file:
        print("debug file not defined in config")
        exit(1)

    try:
        with open(config.file, "a") as amb_raw, open(config.debug_file, "a") as amb_debug:
            while True:
                raw_log_delim = "##############################################"
                data = connection.read()
                decoded_data = data_to_ascii(data)
                Write.to_file(decoded_data, amb_raw)
                decoded_header, decoded_body = decode(data)
                header_msg = ("Decoded Header: {}\n".format(dict_to_ascii(decoded_header)))
                raw_log = "{}\n{}\n{}\n".format(raw_log_delim, header_msg, decoded_body)
                Write.to_file(raw_log, amb_debug)
                if mysql_enabled:
                    if 'TOR' in decoded_body['RESULT'] and decoded_body['RESULT']['TOR'] == 'PASSING':
                        Write.passing_to_mysql(my_cursor, decoded_body)
                        mysql_con.commit()
                sleep(0.1)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to file. Reason: {}".format(e))


if __name__ == "__main__":
    main()
