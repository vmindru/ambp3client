#!/usr/bin/python
from time import sleep
import threading
import time
import socketserver

TIME_PORT = 9999
TIME_IP = '127.0.0.1'


class RefreshTime():
    def __init__(self, connection, refresh_interval=30):
        self.refresh_interval = refresh_interval
        self.connection = connection
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        print("Requesting Decoder Time")
        get_time_msg = bytes.fromhex("8E0000005BEB000024000100040005008F")
        self.connection.write(get_time_msg)
        sleep(self.refresh_interval)


class TCPServer(socketserver.BaseRequestHandler):
    def __init__(self, dt, interval):
        self.dt = dt
        self.interval = interval

    def __call__(self, request, client_address, server):
        h = TCPServer(self.dt, self.interval)
        socketserver.BaseRequestHandler.__init__(h, request, client_address, server)

    def handle(self):
        """ accepts as input RTC timestamp e.g. 1592148824541000
            and sends every interval seconds a incremented TS """
        # while True:
        #     ts_send = self.dt.decoder_time + (round(time.monotonic() * 1000000) - self.dt.monotonic_ts)
        #     msg = f"{ts_send}\n"
        #     self.data = msg.encode()
        #     self.request.sendall(self.data)
        #     sleep(self.interval)
        while True:
            try:
                ts_send = self.dt.decoder_time + (round(time.monotonic() * 1000000) - self.dt.monotonic_ts)
                msg = f"{ts_send}\n"
                self.data = msg.encode()
                self.request.sendall(self.data)
                sleep(self.interval)
            except (ConnectionResetError, BrokenPipeError) as error:
                print("socket connection error: {}".format(error))
                break
            except (KeyboardInterrupt, TypeError) as error:
                print("closing socket, connection: {}".format(error))
                break


class DecoderTime():
    def __init__(self, decoder_time):
        self.decoder_time = decoder_time
        self.monotonic_ts = round(time.monotonic() * 1000000)

    def set_decoder_time(self, decoder_time):
        self.decoder_time = decoder_time
        self.monotonic_ts = round(time.monotonic() * 1000000)


class TimeServer(object):
    def __init__(self, dt, ADDR='127.0.0.1', PORT=9999, interval=1):
        self.dt = dt
        self.ADDR = ADDR
        self.PORT = PORT
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        TCPServer.dt = self.dt
        TCPServer.interval = self.interval
        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer((self.ADDR, self.PORT), TCPServer(self.dt, 0.5))
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

    def stop(self):
        self.server.server_close()


if __name__ == "__main__":
    bg = TimeServer(3)
    while True:
        print("Doing stuff")
        sleep(1)
