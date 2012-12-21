#!/usr/bin/env python
#
# Copyright (c) 2012  Dennis Ideler

import argparse
import logging
from sys import argv
from time import strftime

"""Collects contact info from all schools in British Columbia."""


def set_logger(lvl = None):
    """Sets up logging to a file.
    
    Logging output is appended to the file if it already exists.
    """
    if lvl is None:
        logging.basicConfig(filename = 'bc_schools.log', level = logging.INFO)
    else:
        logging.basicConfig(filename = 'bc_schools.log', level = lvl)

def parse_args():
    parser = argparse.ArgumentParser(
            description = 'Scrape contact info from British Columbia schools.\n'
                          'Log saved in bc_schools.log',
            epilog = 'Happy scraping, use with care!')
    parser.add_argument('--log', type = str, help = 'Log level: debug, info, warning, error, critical')
    args = parser.parse_args()

def main():
    parse_args()
    set_logger(logging.DEBUG) # TODO: Remove argument when ready for production.
    logging.info('Started on %s', strftime("%A, %d %B %Y at %I:%M%p"))
    logging.debug('debug')
    logging.info('info')
    logging.warning('warning')

if __name__ == '__main__':
    main()
