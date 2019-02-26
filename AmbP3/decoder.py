import socket
import codecs

from sys import exit


class Connection:
    def __init__(self, ip, port):
        self.connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.connection.connect((ip, port))
        except ConnectionRefusedError as error:
            print("Can not connect to {}:{}. {}".format(ip, port, error))
            exit(1)
        except (socket.timeout, socket.error) as error:
            print("Error occurred while trying to communicate with  {}:{}".format(ip, port, error))
            exit(1)

    def read(self, bufsize=1024):
        try:
            data = self.connection.recv(bufsize)
        except socket.error:
            print("Error reading from socket")
            exit(1)
        except socket.timeout:
            print("Socket closed while reading")
        if data == b'':
            msg = "No data received, it seems socket got closed"
            print("{}".foramt(msg))
            exit(1)
        data = codecs.encode(data, 'hex')
        data = self._p3_decode(data)
        return data

    def _p3_decode(self, data):
        decoded_data = data.decode('ascii')
        return "{}\n".format(decoded_data)
