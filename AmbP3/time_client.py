#!/usr/bin/python
from time import sleep
import threading
import socket
from AmbP3.time_server import TIME_PORT
from AmbP3.time_server import TIME_IP
from AmbP3.time_server import DecoderTime


class TCPClient():
    def __init__(self, dt, address, port, interval, retry_connect=30):
        self.dt = dt
        self.interval = interval
        self.server_address = (address, port)
        self.retry_connect = retry_connect
        self.connected = False

    def connect(self):
        self.connected = False
        retry = self.retry_connect
        while retry > 1:
            sleep(0.5)
            try:
                print(f"connecting, retry left {retry}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(self.server_address)
                self.connected = True
                retry -= 1
                break
            except (socket.error, socket.timeout) as e:
                print(f"connect failed: {e}")
                self.connected = False
                retry -= 1
        else:
            print("Can not connect, exiting")
            exit(1)

    def read(self):
        retry = self.retry_connect
        data = False
        while retry > 1:
            try:
                data = self.socket.recv(2048)
                self.connected = True
                retry -= 1
                break
            except (socket.error, socket.timeout) as e:
                print(f"read failed, reconnecting: {e}")
                self.connected = False
                retry -= 1
                self.connect()
        return data


class TimeClient(object):
    def __init__(self, dt, ADDR=TIME_IP, PORT=TIME_PORT, interval=1, retry_connect=30):
        """ dt is DecoderTime instance """
        self.dt = dt
        self.ADDR = ADDR
        self.PORT = PORT
        self.retry_connect = retry_connect
        self.interval = interval
        self.tcpclient = TCPClient(self.dt, ADDR, PORT, interval, retry_connect=self.retry_connect)
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            if not self.tcpclient.connected:
                self.tcpclient.connect()
            else:
                try:
                    data = int(self.tcpclient.read().split()[-1])
                    self.dt.decoder_time = data
                except (ValueError, IndexError) as e:
                    self.dt.decoder_time = 0
                    print(f"Failed to reada data: {e}")
                    print(f"reconnecting")
                    self.tcpclient.connected = False
            sleep(0.5)


if __name__ == "__main__":
    dt = DecoderTime(1)
    bg = TimeClient(dt)
    while True:
        print("Doing stuff")
        sleep(1)
