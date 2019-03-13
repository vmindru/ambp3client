import socket
import codecs

from sys import exit
from . import records


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


def p3decode(data):
    def _get_header(data):
        str_header = data[0:10]
        header = {"SOR": str_header[0:1],
                  "Version": str_header[1:2],
                  "Length": str_header[2:4][::-1],  # [::-1] invert the hex ...
                  "CRC": str_header[4:6][::-1],
                  "Flags": str_header[6:8][::-1],
                  "TOR": str_header[8:10][::-1]
                  }
        return header

    def _decode_record(tor, tor_body):
        hex_tor = codecs.encode(tor, 'hex')
        tor_name = records.type_of_records[hex_tor]['tor_name']
        tor_fields = records.type_of_records[hex_tor]['tor_fields']
        general_fields = records.GENERAL
        tor_fields = {**general_fields, **tor_fields}
        tor_body = bytearray(tor_body)
        DECODED = {'TOR': tor_name}
        while len(tor_body) > 0:
            one_byte = tor_body[0:1]
            one_byte_hex = codecs.encode(one_byte, 'hex')
            if one_byte_hex in tor_fields:
                record_attr = tor_fields[one_byte_hex]
            elif one_byte_hex == b'8f':  # records always end in 8f
                tor_body = []
                continue
            else:
                if 'UNDECODED' in DECODED:
                    DECODED['UNDECODED'].append(one_byte_hex)
                else:
                    DECODED['UNDECODED'] = [one_byte_hex]
                del tor_body[:2]
                continue

            record_attr_length = int(codecs.encode(tor_body[1:2], 'hex'))
            record_attr_value = codecs.encode(tor_body[2:2+record_attr_length][::-1], 'hex')
            # print(record_attr, record_attr_length, record_attr_value)
            del tor_body[:2+record_attr_length]
            DECODED[record_attr] = record_attr_value
        return DECODED

    def _decode_body(tor, tor_body):
        result = _decode_record(tor, tor_body)
        return {'RESULT': result}

    def _get_tor_body(data):
        tor_body = data[10:]
        return tor_body

    header = _get_header(data)
    tor = header['TOR']
    tor_body = _get_tor_body(data)
    decoded_body = _decode_body(tor, tor_body)
    return header, decoded_body
