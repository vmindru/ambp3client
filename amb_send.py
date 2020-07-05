#!/usr/bin/env python
from sys import exit
from argparse import ArgumentParser
from time import sleep

from AmbP3.decoder import p3decode
from AmbP3.decoder import Connection

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


def amb_send_msg(hexmsg, ip=ADDR, port=PORT):
    connection = Connection(ip, port)
    connection.connect()
    try:
        connection.write(bytes.fromhex(hexmsg))
        sleep(0.5)
        while True:
            for data in connection.read():
                decoded_header, decoded_body = p3decode(data)  # NEED OT REPLACE WITH LOGGING
            break
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to file. Reason: {}".format(e))
    return decoded_header, decoded_body


def main():
    config = get_args()
    decoded_header, decoded_body = amb_send_msg(config.hexmsg, config.ip, config.port)
    print(decoded_header, decoded_body)


if __name__ == "__main__":
    main()
