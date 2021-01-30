#!/usr/bin/env python3
import argparse
import logging

import config


def set_loglevel():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--log",
        help="Loglevel",
    )
    args = parser.parse_args()
    loglevel = args.log
    if loglevel:
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        config.loglevel = numeric_level
        print(f"Config loglevel set to {numeric_level}")
    else:
        # default to warning
        print("Setting loglevel to 40 in config")
        config.loglevel = 40
