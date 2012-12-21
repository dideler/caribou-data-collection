#!/usr/bin/env python
#
# Copyright (c) 2012  Dennis Ideler

import argparse
import logging
from sys import argv
from time import strftime

"""Collects contact info from all schools in British Columbia.

Examples:
    python bc_schools.py
    python bc_schools.py --help  # Displays the help.
    python bc_schools.py --version  # Displays the program version.
    python bc_schools.py --log=info  # Sets the log level to INFO.
    python bc_schools.py --log info  # Another way to set the log level.

"""


def set_logger(lvl = None):
    """Sets up logging to a file.
    
    Logging output is appended to the file if it already exists.
    """
    #lvl = getattr()
    # TODO: convert argument to a log level, see example
    if lvl is None:
        logging.basicConfig(filename = 'bc_schools.log', level = logging.INFO)
    else:
        logging.basicConfig(filename = 'bc_schools.log', level = lvl)

def parse_args():
    parser = argparse.ArgumentParser(
            description = 'Scrape contact info from British Columbia schools.\n'
                          'Log saved in bc_schools.log',
            epilog = 'Happy scraping, use with care!')
    parser.add_argument('--log', default = 'info', dest = 'loglevel',
            help = 'Log level (default: %(default)s)',
            choices = ['debug', 'info', 'warning', 'error', 'critical'])
    parser.add_argument('-v, --version', action = 'version',
            version = '%(prog)s 1.0')
    args = parser.parse_args()
    print args
    print args.loglevel

def main():
    parse_args()
    set_logger(logging.DEBUG) # TODO: Remove argument when ready for production.
    logging.info('Started on %s', strftime("%A, %d %B %Y at %I:%M%p"))
    logging.debug('debug')
    logging.info('info')
    logging.warning('warning')

if __name__ == '__main__':
    main()
