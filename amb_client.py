#!/usr/bin/env python
from time import sleep
from sys import exit

from AmbP3.config import Config
from AmbP3.decoder import Connection
from AmbP3.write import Write


def main():
    config = Config()
    print(vars(config))
    connection = Connection.read(config.ip, config.port)
    if not config.file:
        print("file not defined in config")
        exit(1)

    try:
        with open(config.file, "wb") as file_handler:
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
