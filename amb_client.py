#!/usr/bin/env python
from time import sleep
from sys import exit

from AmbP3.config import Config
from AmbP3.decoder import Connection
from AmbP3.decoder import split as decode
from AmbP3.decoder import bin_data_to_ascii as data_to_ascii
from AmbP3.decoder import bin_dict_to_ascii as dict_to_ascii
from AmbP3.write import Write


def main():
    config = Config()
    print(vars(config))
    connection = Connection(config.ip, config.port)
    connection.connect()
    if not config.file:
        print("file not defined in config")
        exit(1)

    try:
        with open(config.file, "a") as file_handler:
            while True:
                data = connection.read()
                print("Input Data: {}\nDecoded data: {}\n".format(data_to_ascii(data), dict_to_ascii(decode(data))))
                Write.to_file(data_to_ascii(data), file_handler)
                sleep(0.5)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to {}. Reason: {}".format(file_handler.name(), e))


if __name__ == "__main__":
    main()
