#!/usr/bin/env python
#
# Copyright (c) 2012  Dennis Ideler <ideler.dennis at gmail.com>
# Prepared for Professor Thomas Wolf <twolf at brocku.ca>
# School contact info to be used for the Caribou Cup Mathematics Competition.

import argparse
import logging
from sys import argv
from time import strftime
#from time import sleep  # TODO: use to randomize crawling pattern and to cut the server some slack

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedTagNameException

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
    assert 'School and District Contacts' in browser.title, 'Wrong webpage.'
    # TODO
    # find city-list element - x
    # for each city - x
    #   click city - x
    #   find school-list element
    #   for each school
    #       click school
    #       extract school name
    #               address
    #               city
    #               province (will be 'BC')
    #               postal code
    #               school board
    #               contact name
    #               contact position (e.g. teacher or principal)
    #               email
    #               timezone (will be 'America/Vancouver')
    #               country (will be 'CA')
    
    # NOTE: The page reloads on every option click. Therefore the element will
    #       no longer exist in cache and Selenium will complain.
    #       A workaround is to re-find the element after every option click.

    # This is slightly more efficient than:
    #   city_list = browser.find_element_by_id('citySelect')
    #   city_options = city_list.find_elements_by_tag_name('option')
    try:
        city_list = Select(browser.find_element_by_id('citySelect'))
    except UnexpectedTagNameException:
        print 'Element found is not a SELECT tag.'
    cities = [option.text.strip() for option in city_list.options]
    num_cities = len(cities)
    logging.info("Found %d cities", num_cities-1) # First option is not a city.

    for i in xrange(1, num_cities):
        while True: # This is a dirty hack since Selenium's wait methods aren't working.
            try:
                city_list = Select(browser.find_element_by_id('citySelect'))
                expected_city, actual_city = cities[i], city_list.options[i].text.strip()
                assert expected_city == actual_city, ('Wrong city selected. '
                    'Expected: {}. Actual: {}.').format(expected_city, actual_city)
                logging.info("Crawling city #%d: %s", i, actual_city)
                city_list.select_by_index(i)
            except StaleElementReferenceException:
                # By the time it retries, the element should have loaded.
                continue
            break

        # school list id -> citySchoolSelect

    #browser.back()
    browser.close()

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
