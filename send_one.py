#!/usr/bin/env python
from time import sleep
from sys import exit
from argparse import ArgumentParser

from AmbP3.decoder import p3decode
from AmbP3.decoder import Connection
from AmbP3.decoder import bin_data_to_ascii as data_to_ascii

ADDR = '127.0.0.1'
PORT = 5403


def get_args():
    parser = ArgumentParser()
    parser.add_argument("-H", "--host", help="IP address to bind on",  default=ADDR, dest='ip')
    parser.add_argument("-p", "--listen-port", help="PORT to bind on",  default=PORT, dest='port', type=int)
    parser.add_argument("-w", "--wait", help="wait for data", default=0.5, dest='INTERVAL', type=float)
    parser.add_argument("-m", "--msg", help="hex msg", dest='hexmsg')
    args = parser.parse_args()
    return args


def main():
    print("************ STARTING *******************")
    config = get_args()

    connection = Connection(config.ip, config.port)
    connection.connect()

    try:
        connection.write(bytes.fromhex(config.hexmsg))
        while True:
            raw_log_delim = "##############################################\n\n"
            print(raw_log_delim)
            for data in connection.read():
                decoded_data = data_to_ascii(data)
                decoded_header, decoded_body = p3decode(data)  # NEED OT REPLACE WITH LOGGING
                print(decoded_data)
                print(decoded_header)
                print(decoded_body)
                print("\n\n")
                sleep(2)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to file. Reason: {}".format(e))


if __name__ == "__main__":
    main()
