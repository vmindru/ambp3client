#!/usr/bin/env python
from time import sleep
from sys import exit

from AmbP3.config import get_args
from AmbP3.decoder import Connection
from AmbP3.decoder import p3decode
from AmbP3.decoder import bin_data_to_ascii as data_to_ascii
from AmbP3.decoder import bin_dict_to_ascii as dict_to_ascii
from AmbP3.write import Write
from AmbP3.write import open_mysql_connection
from AmbP3.write import Cursor


def main():
    config = get_args()
    conf = config.conf
    print(conf)
    mysql_enabled = conf['mysql_backend']
    if not mysql_enabled:
        print("ERROR, please configure MySQL")
        exit(1)
    mysql_con = open_mysql_connection(user=conf['mysql_user'],
                                      db=conf['mysql_db'],
                                      password=conf['mysql_password']
                                      )
    cursor = mysql_con.cursor()
    my_cursor = Cursor(mysql_con, cursor)
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
                print(raw_log_delim)
                for data in connection.read():
                    decoded_data = data_to_ascii(data)
                    Write.to_file(decoded_data, amb_raw)  # REPLACE BY LOGGING
                    decoded_header, decoded_body = p3decode(data)  # NEED OT REPLACE WITH LOGGING
                    header_msg = ("Decoded Header: {}\n".format(dict_to_ascii(decoded_header)))
                    raw_log = "{}\n{}\n{}\n".format(raw_log_delim, header_msg, decoded_body)
                    Write.to_file(raw_log, amb_debug)
                    if 'TOR' in decoded_body['RESULT'] and decoded_body['RESULT']['TOR'] == 'PASSING':
                        Write.passing_to_mysql(my_cursor, decoded_body)
                        print(decoded_body)
                    sleep(0.1)
                sleep(0.1)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to file. Reason: {}".format(e))


if __name__ == "__main__":
    main()
