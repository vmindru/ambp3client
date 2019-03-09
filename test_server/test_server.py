#!/usr/bin/env python

import socket
from time import sleep
from argparse import ArgumentParser

INPUT_FILE = "amb.out"
ADDR = '127.0.0.1'
PORT = 12000


def get_args():
    parser = ArgumentParser()
    parser.add_argument("file", help="amb.out HEX file location", default=INPUT_FILE, nargs='?')
    parser.add_argument("-l", "--listen-address", help="IP address to bind on",  default=ADDR)
    parser.add_argument("-p", "--listen-port", help="PORT to bind on",  default=PORT)
    args = parser.parse_args()
    return args


def create_sock(ADDR, PORT):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ADDR, PORT))
    s.listen(1)
    print("Listening, waiting for connection")
    conn, addr = s.accept()
    print("Accepted connection")
    return conn, s


def hex_to_binary(data):
    bin_str = bin(int(data, 16))
    byte_str = int(bin_str, 2).to_bytes((len(bin_str)//8), 'big')
    return byte_str


def send_net():
    conn, s = create_sock(ADDR, PORT)
    with open(INPUT_FILE, "r") as fd:
        while True:
            data = "{}".format(fd.readline()).rstrip()
            data = hex_to_binary(data)
            try:
                conn.send(data)
                sleep(1)
            except (ConnectionResetError, BrokenPipeError) as error:
                print("socket connection error: {}".format(error))
                conn.close()
                s.close()
                break
            except (KeyboardInterrupt, TypeError) as error:
                print("closing socket, connection: {}".format(error))
                conn.close()
                s.close()
                break

    conn.close()
    s.close()


while True:
    arts = get_args()
    print("Starting server")
    send_net()
    sleep(0.5)
