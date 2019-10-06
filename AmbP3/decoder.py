import socket
import codecs


from sys import exit
from . import records
from .logs import Logg

logger = Logg.create_logger('decoder')


class Connection:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket()

    def connect(self):
        try:
            self.socket.connect((self.ip, self.port))
        except ConnectionRefusedError as error:
            logger.error("Can not connect to {}:{}. {}".format(self.ip, self.port, error))
            exit(1)
        except (socket.timeout, socket.error) as error:
            logger.error("Error occurred while trying to communicate with  {}:{}".format(self.ip, self.port, error))
            exit(1)

    def split_records(self, data):
        """some times server send 2 records in one message
           concatinated, you can find those by '8f8e' EOR and SOR next to eahc other"""
        byte_array = bytearray(data)
        size = len(byte_array)
        split_data = [bytearray()]
        for index, byte in enumerate(byte_array):
            if index != size-1 and byte == 143 and byte_array[index+1] == 142:
                print("found delimeter byte 143,142 b'8f8e'")
                split_data[-1].append(byte)
                split_data.append(bytearray())
                print("start new record")
            else:
                split_data[-1].append(byte)
        return split_data

    def read(self, bufsize=1024):
        try:
            data = self.socket.recv(bufsize)
        except socket.error:
            logger.error("Error reading from socket")
            exit(1)
        except socket.timeout:
            logger.error("Socket closed while reading")
        if data == b'':
            msg = "No data received, it seems socket got closed"
            logger.info("{}".format(msg))
            self.socket.close()
            exit(1)
        return self.split_records(data)


def bin_to_decimal(bin_data):
    return int(bin_data.decode(), 16)


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
    def _validate(data):
        "perform validation checks and return ready to process data or None"
        data = _check_crc(data) if data is not None else None
        print("P3decode function decodint: {}".format(data.hex()))
        data = _unescape(data) if data is not None else None
        data = _check_length(data) if data is not None else None
        return data

    def _check_crc(data):
        "check CRC integrity"
        return data

    def _unescape(data):
        "If the value is 0x8d, 0x8e or 0x8f and it's not the first or last byte of the message,\
         the value is prefixed/escaped by 0x8D followed by the byte value plus 0x20."
        new_data = bytearray(data)[1:-1]  # first and last character should not be escaped
        escaped_data = bytearray()
        escape_next = False
        for byte in new_data:
            if escape_next:
                escaped_data.append(byte - 20)
                escape_next = False
                continue
            if byte in [141, 141, 142]:
                escape_next = True
            else:
                escaped_data.append(byte)
        escaped_data.insert(0, 142)  # INSERT THE SOR Start of Record
        escaped_data.append(143)  # INSERT THE EOR End of Record
        return bytes(escaped_data)

    def _lunescape(data):
        "If the value is 0x8d, 0x8e or 0x8f and it's not the first or last byte of the message,\
         the value is prefixed/escaped by 0x8D followed by the byte value plus 0x20."
        new_data = bytearray(data)
        for byte_number in list(range(1, len(data)-1)):
            byte = data[byte_number:byte_number+1]
            if codecs.encode(byte, 'hex') in [b'8d', b'8e', b'8f']:
                new_data[byte_number+1] = data[byte_number+1]-int('0x20', 16)
                del new_data[byte_number]

        data = bytes(new_data)
        return data

    def _check_length(data):
        "check if data is of correct length"
        return data

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
        logger.info("tor:{} converted to hex_tor: {}".format(tor, hex_tor))
        if hex_tor in records.type_of_records:
            tor_name = records.type_of_records[hex_tor]['tor_name']
            tor_fields = records.type_of_records[hex_tor]['tor_fields']
            DECODED = {'TOR': tor_name}
        else:
            print("{} record_type uknown".format(hex_tor))
            return {'undecode_tor_body': tor_body}

        general_fields = records.GENERAL
        tor_fields = {**general_fields, **tor_fields}
        tor_body = bytearray(tor_body)
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
            del tor_body[:2+record_attr_length]
            DECODED[record_attr] = record_attr_value
        return DECODED

    def _decode_body(tor, data):
        tor_body = _get_tor_body(data)
        try:
            result = _decode_record(tor, tor_body)
            return {'RESULT': result}
        except ValueError:
            print("DECODE FAILED. TOR: {}, TOR_BODY: {}".format(tor, tor_body))
            return {'RESULT': {}}

    def _get_tor_body(data):
        tor_body = data[10:]
        return tor_body

    data = _validate(data)
    if data is not None:
        decoded_header = _get_header(data)
        tor = decoded_header['TOR']
        decoded_body = _decode_body(tor, data)
        return decoded_header, decoded_body
    else:
        return data, data
