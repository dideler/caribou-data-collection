#!/usr/bin/env python
#
# Copyright (c) 2012  Dennis Ideler <ideler.dennis at gmail.com>
# Prepared for Professor Thomas Wolf <twolf at brocku.ca>
# School contact info to be used for the Caribou Cup Mathematics Competition.

import argparse
import logging
from sys import argv
from time import strftime
from time import sleep  # Randomize crawling pattern and give server some slack.
from random import randint
from urllib import pathname2url

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedTagNameException

"""Collects contact info from all schools in British Columbia.

There is an option to specify a maximum time (in seconds) to wait between page
requests. This option is useful for randomizing the crawling patterns, which
makes it less obvious that the crawling is performed by a bot. It also reduces
the load on the server(s) by spreading out the requests over a longer period.

Examples:
    python bc_schools.py
    python bc_schools.py --help
    python bc_schools.py --version
    python bc_schools.py --log=info
    python bc_schools.py --log info
    python bc_schools.py --max-pause 5
    python bc_schools.py --append
"""

class Crawler(object):
    """A crawler that collects contact info of all K12 schools in BC, Canada.

    Attributes:
    - base_url: The URL of the website that contains the school directories.
    - home_url: The homepage of the website.
    - seconds: The maximum amount of seconds to wait between page requests.
    """

    def __init__(self, url, secs):
        """Inits Crawler with the proper URLs and an empty browser driver."""
        self.base_url = url
        self.home_url = url + 'Home.do'
        self.seconds = secs
        self._browser = None
        self._tablerow_xpath = '/html/body/div/table[3]/tbody/tr[1]/td[4]/table[2]/tbody/tr'
        self._leftcol_xpath = self._tablerow_xpath + '/td[1]'
        self._rightcol_xpath = self._tablerow_xpath + '/td[3]'
        self._email_xpath = self._rightcol_xpath + '/a'

    def crawl(self):
        """Crawls the website and extracts the information of all BC schools."""
        self._browser = webdriver.Chrome()
        self._browser.get(self.home_url)
        assert 'School and District Contacts' in self._browser.title, 'Wrong webpage.'
        
        # NOTE: The page reloads on every option click. Thus the element will
        #       no longer exist in cache and Selenium will complain and crash.
        #       A workaround is to re-find the element after every page reload.

        self.__crawl_cities()
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
            sleep(randint(0, self.seconds)) # Randomly pause between requests.
            self._browser.get(city_url)
            self.__crawl_schools_in_city(city)
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

    def __crawl_schools_in_city(self, city):
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
            school_name, school_value = school[0], school[1]
            school_url = self.base_url + school_value
            logging.info("\tCrawling school %d: %s", i, school_name)
            sleep(randint(0, self.seconds)) # Randomly pause between requests.
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
            # entry, the filemode has to be append. If the performance suffers
            # too greatly, open the file before crawling and close it when
            # completed, though this will complicate error handling.
            with open('bc-schools.csv', 'a') as csv_file:
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

def set_logger(loglevel, file_mode):
    """Sets up logging to a file.
    
    Logging output is appended to the file if it already exists.
    """
    numlevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numlevel, int):  # Should never happen due to argparse.
        raise ValueError('Invalid log level: ', loglevel)
    logging.basicConfig(format = '%(asctime)s %(levelname)s: %(message)s',
            datefmt = '%I:%M:%S',  # Add %p for AM or PM.
            filename = 'bc_schools.log',
            filemode = file_mode,
            level = numlevel)

def parse_args():
    parser = argparse.ArgumentParser(
        description = 'Scrape contact info from British Columbia schools.\n'
                      'Log saved in bc_schools.log',
        epilog = 'Happy scraping, use with care!')
    parser.add_argument('--log', default = 'info', dest = 'loglevel',
                        help = 'Log level (default: %(default)s)',
                        choices = ['debug', 'info', 'warning', 'error',
                                   'critical'])
    parser.add_argument('--max-pause', type = int, default = 0, dest = 'seconds',
                        help = 'Maximum amount of seconds to pause between '
                                'page requests (default: %(default)s sec)')
    parser.add_argument('-a', '--append', action = 'store_const', const = 'a',
                        default = 'w', dest = 'filemode',
                        help = 'Append to the log file instead of overwriting it.')
    parser.add_argument('-u', '--unique', action = 'store_true',
                        help = 'Output file will contain unique data')
    parser.add_argument('-v, --version', action = 'version',
                        version = '%(prog)s 1.0')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    set_logger(args.loglevel, args.filemode)
    logging.info('Started on %s', strftime("%A, %d %B %Y at %I:%M%p"))
    logging.info('Log level = %s, Max seconds to pause = %d, File mode = %s',
                 args.loglevel, args.seconds, args.filemode)
    crawler = Crawler('http://www.bced.gov.bc.ca/apps/imcl/imclWeb/',
                      args.seconds)
    crawler.crawl()

if __name__ == '__main__':
    main()
