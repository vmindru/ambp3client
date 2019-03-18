#!/usr/bin/env python
from time import sleep
from sys import exit
from argparse import ArgumentParser

from AmbP3.config import Config
from AmbP3.decoder import Connection
from AmbP3.decoder import p3decode as decode
from AmbP3.decoder import bin_data_to_ascii as data_to_ascii
from AmbP3.decoder import bin_dict_to_ascii as dict_to_ascii
from AmbP3.write import Write


def get_args(config):
    PORT = config.port
    IP = config.ip
    """ args that overwrite AmbP3.config """
    port_help_msg = "PORT for AMB decoder. Default {}".format(PORT)
    server_help_msg = "ip address of AMB decoder. Default {}".format(IP)
    args = ArgumentParser()
    args.add_argument("-p", "--port", default=PORT, type=int, help=port_help_msg)
    args.add_argument("-a", "--address", dest="ip", default=IP, help=server_help_msg)
    cli_args = args.parse_args()
    config.ip = cli_args.ip
    config.port = cli_args.port
    return config


def main():
    config = Config()
    config = get_args(config)
    connection = Connection(config.ip, config.port)
    connection.connect()
    if not config.file:
        print("file not defined in config")
        exit(1)
    elif not config.debug_file:
        print("debug file not defined in config")
        exit(1)

    try:
        with open(config.file, "a") as amb_raw, open(config.debug_file, "a") as amb_debug:
            while True:
                data = connection.read()
                decoded_data = data_to_ascii(data)
                decoded_header, decoded_body = decode(data)
                input_msg = ("Input Data: {}\n".format(decoded_data))
                header_msg = ("Decoded Header: {}\n".format(dict_to_ascii(decoded_header)))
                print("{}{}{}".format(input_msg, header_msg, decoded_body))
                raw_log_delim = "##############################################"
                raw_log = "{}\n{}\n{}\n".format(raw_log_delim, header_msg, decoded_body)
                Write.to_file(data_to_ascii(data), amb_raw)
                Write.to_file(raw_log, amb_debug)
                sleep(0.1)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to file. Reason: {}".format(e))


if __name__ == "__main__":
    main()
