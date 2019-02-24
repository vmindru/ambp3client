#!/usr/bin/env python
from AmbP3 import Config
from AmbP3 import Decoder
from AmbP3 import Write
from time import sleep
from sys import exit


def main():
    config = Config()
    print(vars(config))
    connection = Decoder.connection(config.ip, config.port)
    if not config.file:
        print("file not defined in config")
        exit(1)

    try:
        with open(config.file, "a") as file_handler:
            while True:
                data = connection.read()
                print(data)
                Write.to_file(data, file_handler)
                sleep(0.5)
    except KeyboardInterrupt:
        print("Closing")
        exit(0)
    except IOError as e:
        print("error writing to {}. Reason: {}".format(file_handler.name(), e))


if __name__ == "__main__":
    main()
