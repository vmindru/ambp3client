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
        return data


def bin_data_to_ascii(bin_data):
    "Converts binary input HEX data into ascii"
    data = codecs.encode(bin_data, 'hex')
    decoded_data = data.decode('ascii')
    return "{}".format(decoded_data)


def bin_dict_to_ascii(dict):
    "takes as input Dict with Binary values, converts into ascii, returns covnerted dict"
    for key, value in dict.items():
        dict[key] = bin_data_to_ascii(value)
    return dict


def _byte_reorder():
    pass


def split(data):
    def _get_header(data):
        str_header = data[0:10]
        header = {"SOR": str_header[0:1],
                  "Version": str_header[1:2],
                  "Length": str_header[2:4][::-1],
                  "CRC": str_header[4:6][::-1],
                  "Flags": str_header[6:8][::-1],
                  "TOR": str_header[8:10][::-1]
                  }
        return header

    def _get_tor_body(data):
        tor_body = data[10:]
        body = {"DATA": tor_body}
        return body

    return _get_header(data), _get_tor_body(data)
