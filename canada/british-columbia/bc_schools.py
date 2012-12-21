#!/usr/bin/env python
#
# Copyright (c) 2012  Dennis Ideler

import argparse
import logging
from sys import argv
from time import strftime

from selenium import webdriver

"""Collects contact info from all schools in British Columbia.

Examples:
    python bc_schools.py
    python bc_schools.py --help  # Displays the help.
    python bc_schools.py --version  # Displays the program version.
    python bc_schools.py --log=info  # Sets the log level to INFO.
    python bc_schools.py --log info  # Another way to set the log level.

"""

def extract(url):
    """Extracts the information of all BC schools.

    TODO: might have to split this up into multiple functions...
    """
    browser = webdriver.Chrome()
    browser.get(url)

def set_logger(loglevel):
    """Sets up logging to a file.
    
    Logging output is appended to the file if it already exists.
    """
    numlevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numlevel, int):  # Should never happen due to argparse.
        raise ValueError('Invalid log level: ', loglevel)
    logging.basicConfig(format = '%(asctime)s %(levelname)s: %(message)s',
            datefmt = '%I:%M:%S',  # Add %p for AM or PM.
            filename = 'bc_schools.log',
            level = numlevel)  # Add filemode='w' to overwrite old log file.

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
    return args

def main():
    args = parse_args()
    set_logger(args.loglevel)
    logging.info('Started on %s', strftime("%A, %d %B %Y at %I:%M%p"))
    extract('http://www.bced.gov.bc.ca/apps/imcl/imclWeb/Home.do')

if __name__ == '__main__':
    main()
