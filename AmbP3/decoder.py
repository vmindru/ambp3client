import socket
import codecs

from sys import exit


class Connection:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket()

    def connect(self):
        try:
            self.socket.connect((self.ip, self.port))
        except ConnectionRefusedError as error:
            print("Can not connect to {}:{}. {}".format(self.ip, self.port, error))
            exit(1)
        except (socket.timeout, socket.error) as error:
            print("Error occurred while trying to communicate with  {}:{}".format(self.ip, self.port, error))
            exit(1)

    def read(self, bufsize=1024):
        try:
            data = self.socket.recv(bufsize)
        except socket.error:
            print("Error reading from socket")
            exit(1)
        except socket.timeout:
            print("Socket closed while reading")
        if data == b'':
            msg = "No data received, it seems socket got closed"
            print("{}".format(msg))
            self.socket.close()
            exit(1)
        data = codecs.encode(data, 'hex')
        data = self._p3_decode(data)
        return data

    def _p3_decode(self, data):
        decoded_data = data.decode('ascii')
        return "{}\n".format(decoded_data)


def split(data):
    def _get_header(data):
        str_header = data[0:20]
        header = {"SOR": str_header[0:2],
                  "Version": str_header[2:4],
                  "Length": str_header[4:8][::-1],
                  "CRC": str_header[8:12][::-1],
                  "Flags": str_header[12:16][::-1],
                  "TOR": str_header[16:20][::-1]
                  }
        return header
    return _get_header(data)
