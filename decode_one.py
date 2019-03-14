#!/usr/bin/env python
from argparse import ArgumentParser
from AmbP3.decoder import p3decode as decode
from AmbP3.decoder import bin_dict_to_ascii as dict_to_ascii

DEFAULT_DATA = "8e023300c922000001000104a468020003042f79340004087802cd052083050005\
02990006021c00080200008104131804008f"


def get_args():
    args = ArgumentParser()
    args.add_argument("data", default=DEFAULT_DATA, nargs="?")
    return args.parse_args()


def hex_to_binary(data):
    bin_str = bin(int(data, 16))
    byte_str = int(bin_str, 2).to_bytes((len(bin_str)//8), 'big')
    return byte_str


def main():
    args = get_args()
    data = args.data.rstrip()
    result = decode(hex_to_binary(data))
    header = dict_to_ascii(result[0])
    body = dict_to_ascii(result[1])
    return header, body


if __name__ == "__main__":
    print(main())
