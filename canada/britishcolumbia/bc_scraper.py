#!/usr/bin/env python
#
# Copyright (c) 2012-2013  Dennis Ideler <ideler.dennis at gmail.com>
# Prepared for Professor Thomas Wolf <twolf at brocku.ca>
# School contact info to be used for the Caribou Cup Mathematics Competition.

import argparse
import logging
import sys
import time
import random
import urllib

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedTagNameException

try:
    from utils import io
except ImportError:
    # Executed as standalone script. Add toplevel dir to python path.
    from os import path as ospath
    from sys import path as syspath
    parentdir = ospath.dirname(ospath.dirname(ospath.dirname(ospath.abspath(__file__))))
    syspath.insert(0, parentdir)
    from utils import io

"""Collects contact info from all schools in British Columbia.

There is an option to specify a maximum time (in seconds) to wait between page
requests. This option is useful for randomizing the scraping patterns, which
makes it less obvious that the scraping is performed by a bot. It also reduces
the load on the server(s) by spreading out the requests over a longer period.

Examples:
    python bc_schools.py
    python bc_schools.py --help
    python bc_schools.py --version
    python bc_schools.py --log=info
    python bc_schools.py --log info
    python bc_schools.py --max-pause 5
    python bc_schools.py --append
    python bc_schools.py --unique
"""

region = 'britishcolumbia'  # Region/state/province/etc.

class Scraper(object):
    """A scraper that collects contact info of all K12 schools in BC, Canada.

    Attributes:
    - base_url: URL of the website that contains the school directories.
    - home_url: Homepage of the website.
    - seconds: Maximum amount of seconds to wait between page requests.
    - output: Output file path that will contain the extracted data.
    """

    def __init__(self, url, secs, out):
        """Inits Scraper with the proper URLs and an empty browser driver."""
        self.base_url = url
        self.home_url = url + 'Home.do'
        self.seconds = secs
        self.output = out
        self._browser = None
        self._tablerow_xpath = '/html/body/div/table[3]/tbody/tr[1]/td[4]/table[2]/tbody/tr'
        self._leftcol_xpath = self._tablerow_xpath + '/td[1]'
        self._rightcol_xpath = self._tablerow_xpath + '/td[3]'
        self._email_xpath = self._rightcol_xpath + '/a'

    def scrape(self):
        """Scrapes website and extracts the contact info of all schools."""
        self._browser = webdriver.Chrome()
        self._browser.get(self.home_url)
        assert 'School and District Contacts' in self._browser.title, 'Wrong webpage.'
        
        # NOTE: The page reloads on every option click. Thus the element will
        #       no longer exist in cache and Selenium will complain and crash.
        #       A workaround is to re-find the element after every page reload.

        self.__scrape_cities()
        self._browser.close()

    def __scrape_cities(self):
        # `Select` is more efficient than `find_elements_by_tag_name('option')`
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

        # Dynamically create the city URLs and scrape each city.
        for i, city in enumerate(cities):
            if i == 0: continue # First city option is "City", skip it.
            city_query = '?city={}'.format(urllib.pathname2url(city))
            city_url = self.home_url + city_query
            logging.info("Scraping city %d: %s", i, city)
            time.sleep(random.randint(0, self.seconds))
            self._browser.get(city_url)
            self.__scrape_schools_in_city(city)

    def __scrape_schools_in_city(self, city):
        try:
            school_list = Select(self._browser.find_element_by_id('citySchoolSelect'))
        except UnexpectedTagNameException:
            logging.critical('citySchoolSelect element is not a SELECT tag.')
        except StaleElementReferenceException:
            logging.critical('citySchoolSelect element does not exist.')

        # Create a list of tuples for each school -> (school name, school value)
        # This allows for scraping without using the school_list element
        # (which ceases to exist in memory when the page changes).
        schools = [(option.text.strip(), option.get_attribute('value')) for option in school_list.options]
        num_schools = len(schools)
        logging.info("Found %d schools", num_schools-1) # First option is not a school.

        # Dynamically create the school URLs and scrape the schools in the city.
        # This strategy is _much_ quicker than clicking every school option
        # in the dropdown list, loop-waiting until the page loads, going back
        # to the previous page using the page history, and repeating.
        for i, school in enumerate(schools):
            if i == 0: continue # First school option is "School Name", skip it.
            school_name, school_value = school[0], school[1]
            school_url = self.base_url + school_value
            logging.info("\tScraping school %d: %s", i, school_name)
            time.sleep(random.randint(0, self.seconds))
            self._browser.get(school_url)
            self.__extract_contact_info(school_name, city)

    def __extract_contact_info(self, schoolname, cityname):
        """Extract contact info for schools with an email address available.

        - If a school has no email address, it is skipped.
        - The contact info is written to a file in comma-separated-values.
        - Though it's probably not needed, all data has its whitespace stripped.
        - Many addresses are actually PO box addresses.
        - Contact field is either "Contact" or "Principal".

        IMPORTANT: Make sure the CSV data matches up with the schools db table.
        """
        school = 'null'
        name = schoolname
        address = None
        city = cityname
        province = 'BC'
        postal_code = None
        schoolboard = 'null'
        contact = None
        phone = None
        position = None
        email = None
        timezone = 'America/Vancouver'
        country = 'CA'

        # The contact information is stored in two table columns. Inside each
        # column, information is separated by newlines. Long email addresses can
        # contain a newline, so if we separate all contact data by newlines, we
        # would misidentify some of the longer email addresses. To prevent this,
        # we look at the mailto link for the full email address.
        email = self._browser.find_element_by_xpath(self._email_xpath).get_attribute('href')[7:]
        if email:
            # A full left column has length 8. Index 0 is empty.
            # A full right column has length 5. Indexes 0, 1 are empty.
            left_col_data = self._browser.find_element_by_xpath(self._leftcol_xpath).text.split('\n')
            right_col_data = self._browser.find_element_by_xpath(self._rightcol_xpath).text.split('\n')

            try:
                full_address = left_col_data[2].split(',')
                address = full_address[0].strip()
                postal_code = full_address[3].strip()  # Strip needed here.
            except IndexError: address = postal_code = 'N/A'
            try:
                contact_person = left_col_data[3].split(' - ')
                position = contact_person[0].strip()
                contact = contact_person[1].strip()
            except IndexError: position, contact = 'N/A', ''
            try: phone = right_col_data[2].strip()
            except IndexError: phone = 'null'
            try: fax = right_col_data[3].strip()
            except IndexError: fax = 'null'

            # There is extra data that we are not extracting, for example:
            #  school type, grades offered, private or public, enrolment date,
            #  phone number, and fax number
            
            # Because this file is constantly being opened and closed for every
            # entry, the filemode HAS to be append. If the performance suffers
            # too greatly, open the file before scraping and close it when
            # completed, though this will complicate error handling.
            with open(self.output, 'a') as csv_file:
                csv_file.write('{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(
                                school, name, address, city, province,
                                postal_code, schoolboard, contact, phone,
                                position, email, timezone, country))

            print ('school id = {}\n'
                   'school name = {}\n'
                   'address = {}\n'
                   'city = {}\n'
                   'province = {}\n'
                   'postal code = {}\n'
                   'schoolboard = {}\n'
                   'contact name = {}\n'
                   'contact phone = {}\n'
                   'contact position = {}\n'
                   'contact email = {}\n'
                   'timezone = {}\n'
                   'country = {}').format(school, name, address, city, province,
                                          postal_code, schoolboard, contact,
                                          phone, position, email, timezone,
                                          country)

            print '--------------------'
        else:
            print 'no email found\n--------------------'

def set_logger(loglevel, file_mode, path):
    """Sets up logging to a file.
    
    Logging output is appended to the file if it already exists.
    """
    numlevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numlevel, int):  # Should never happen due to argparse.
        raise ValueError('Invalid log level: ', loglevel)
    logging.basicConfig(format = '%(asctime)s %(levelname)s: %(message)s',
            datefmt = '%I:%M:%S',  # Add %p for AM or PM.
            filename = path + region + '.log',
            filemode = file_mode,
            level = numlevel)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Scrape contact info from British Columbia schools.',
        epilog='Happy scraping, use with care!')
    parser.add_argument('--log', default='info', dest='loglevel',
                        help='Log level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error', 'critical'])
    parser.add_argument('--max-pause', type=int, default=0, dest='seconds',
                        help='Maximum amount of seconds to pause between '
                             'page requests (default: %(default)s sec)')
    parser.add_argument('-a', '--append', action='store_const', const='a',
                        default='w', dest='filemode',
                        help='Append to the log file instead of overwriting it')
    parser.add_argument('-u', '--unique', action='store_true',
                        help='Output file will contain unique data')
    parser.add_argument('-o', '--output', type=str, default=region,
                        help='Specify the output filename (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version = '%(prog)s 1.0')
    args = parser.parse_args()
    args.output = args.output.replace('.csv', '') + time.strftime('-%b-%d-%Y.csv')
    return args

def main():
    args = parse_args()
    
    if io.dir_exists('logs'):
        logpath = io.datapath
    if io.dir_exists('data'):
        datapath = io.datapath + args.output
    else:
        print 'You need a data directory to continue.'
        sys.exit(1)
    
    set_logger(args.loglevel, args.filemode, logpath)
    logging.info('Started on %s', time.strftime("%A, %d %B %Y at %I:%M%p"))
    logging.info('Log level = %s, Max seconds to pause = %d, File mode = %s',
                 args.loglevel, args.seconds, args.filemode)
    scraper = Scraper('http://www.bced.gov.bc.ca/apps/imcl/imclWeb/',
                      args.seconds, datapath)
    scraper.scrape()
    
    if args.unique:
        io.remove_dupes(datapath)

if __name__ == '__main__':
    # Allow for this module to be run as a script (e.g. python bc_schools.py)
    # Note: This conditional is false when the module is imported.
    main()
