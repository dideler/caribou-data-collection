#!/usr/bin/env python
#
# Copyright (c) 2012  Dennis Ideler <ideler.dennis at gmail.com>
# Prepared for Professor Thomas Wolf <twolf at brocku.ca>
# School contact info to be used for the Caribou Cup Mathematics Competition.

import argparse
import logging
from sys import argv
from time import strftime
from time import sleep  # Used to randomize crawling pattern and to cut the server some slack.
from random import randint
from urllib import pathname2url

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
    python bc_schools.py --max-pause 5  # Wait up to 5 seconds between schools.

"""
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

class Crawler(object):
    """A crawler that collects contact info of all K12 schools in BC, Canada.

    Attributes:
    - base_url: The URL of the website that contains the school directories.
    - home_url: The homepage of the website.
    """

    def __init__(self, url):
        """Inits Crawler with the proper URLs and an empty browser driver."""
        self.base_url = url
        self.home_url = url + 'Home.do'
        self._browser = None

    def crawl(self):
        """Crawls the website and extracts the information of all BC schools."""
        self._browser = webdriver.Chrome()
        self._browser.get(self.home_url)
        assert 'School and District Contacts' in self._browser.title, 'Wrong webpage.'
        
        # NOTE: The page reloads on every option click. Therefore the element will
        #       no longer exist in cache and Selenium will complain.
        #       A workaround is to re-find the element after every option click.

        self.__crawl_cities()
        #browser.back()
        self._browser.close()

    def __crawl_cities(self):
        # Using Select is slightly more efficient than:
        #   city_list = browser.find_element_by_id('citySelect')
        #   city_options = city_list.find_elements_by_tag_name('option')
        try:
            city_list = Select(self._browser.find_element_by_id('citySelect'))
        except UnexpectedTagNameException:
            logging.critical('citySelect element is not a SELECT tag.')
        except StaleElementReferenceException:
            logging.critical('citySelect element does not exist.')
        # Currently it makes no difference using the option's text or value,
        # but it's safer to use the value as it's used for the query.
        # To use the option's text, return option.text.strip() in the loop.
        cities = [option.get_attribute('value') for option in city_list.options]
        num_cities = len(cities)
        logging.info("Found %d cities", num_cities-1) # First option is not a city.

        # Dynamically create the city URLs and crawl each city.
        for i, city in enumerate(cities):
            if i == 0: continue # First city option is "City", skip it.
            city_query = '?city={}'.format(pathname2url(city))
            city_url = self.home_url + city_query
            logging.info("Crawling city %d: %s", i, city)
            self._browser.get(city_url)
            self.__crawl_schools_in_city()
        ''' The above method of iterating through cities is much quicker than:
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
        '''

    def __crawl_schools_in_city(self):
        try:
            school_list = Select(self._browser.find_element_by_id('citySchoolSelect'))
        except UnexpectedTagNameException:
            logging.critical('citySchoolSelect element is not a SELECT tag.')
        except StaleElementReferenceException:
            logging.critical('citySchoolSelect element does not exist.')
        # Create a list of tuples for each school -> (school name, school value)
        # This allows for crawling without using the school_list element
        # (which ceases to exist in memory when the page changes).
        schools = [(option.text.strip(), option.get_attribute('value')) for option in school_list.options]
        num_schools = len(schools)
        logging.info("Found %d schools", num_schools-1) # First option is not a school.

        # Dynamically create the school URLs and crawl the schools in the city.
        # This strategy is _much_ quicker than clicking every school option
        # in the dropdown list, loop-waiting until the page loads, going back
        # to the previous page using the page history, and repeating.
        for i, school in enumerate(schools):
            if i == 0: continue # First school option is "School Name", skip it.
            school_url = self.base_url + school[1]
            logging.info("Crawling school %d: %s", i, school[0])
            self._browser.get(school_url)

    def __extract_contact_info(self):
        """TODO:
        school (primary key, not null, auto increment?): table id, do we have to provide it?
        name (not null): pass in from crawl_schools_in_city()
        address (not null): extract from table data -- will be a PO box!
        city (not null): pass in from crawl_cities() OR extract from table data
        province (not null): 'BC' OR can be extracted from table data
        postal_code (not null): extract from table data
        schoolboard (default null): ???
        contact (default null): extract from table data (if available)
        position (default null): extract from table data (if available)
        email (default null):  extract from table data (if available)
        timezone (default null): "America/Vancouver"
        country (default CA): "CA" OR can be left empty (because CA is default)

        TIPS:
        - strip all text
        - left_col_data = b.find_element_by_xpath('/html/body/div/table[3]/tbody/tr[1]/td[4]/table[2]/tbody/tr/td[1]').text.split('\n')
          that gets you the dirty data in a list, still need to clean it up
          - address
          - contact (name and position)
          - type of school
        - xpath for right_col_data '/html/body/div/table[3]/tbody/tr[1]/td[4]/table[2]/tbody/tr/td[3]'
          - phone
          - fax
          - email
        - many addresses are PO box addresses
        - contact field will either be "Contact" or "Principal"
        """



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
            filemode = 'w',  # Overwrite file if exists -- default is append.
            level = numlevel)

def parse_args():
    parser = argparse.ArgumentParser(
            description = 'Scrape contact info from British Columbia schools.\n'
                          'Log saved in bc_schools.log',
            epilog = 'Happy scraping, use with care!')
    parser.add_argument('--log', default = 'info', dest = 'loglevel',
            help = 'Log level (default: %(default)s)',
            choices = ['debug', 'info', 'warning', 'error', 'critical'])
    parser.add_argument('--max-pause', type = int, default = '0', dest = 'pausetime',
            help = 'Maximum possible time for pausing between HTTP requests (default: %(default)s)')
    parser.add_argument('-v, --version', action = 'version',
            version = '%(prog)s 1.0')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    set_logger(args.loglevel)
    logging.info('Started on %s', strftime("%A, %d %B %Y at %I:%M%p"))
    crawler = Crawler('http://www.bced.gov.bc.ca/apps/imcl/imclWeb/')
    crawler.crawl()

if __name__ == '__main__':
    main()
