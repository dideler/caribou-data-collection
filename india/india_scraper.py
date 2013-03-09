#!/usr/bin/env python
#
# Copyright (c)2013  Dennis Ideler <ideler.dennis at gmail.com>
# Prepared for Professor Thomas Wolf <twolf at brocku.ca>
# School contact info to be used for the Caribou Cup Mathematics Competition.

import argparse
import collections
import logging
import math
import random
import re
import string
import sys
import time
import urllib

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedTagNameException
from selenium.common.exceptions import NoSuchElementException

try:
    from utils import io
except ImportError:
    # Executed as standalone script. Add toplevel dir to python path.
    from os import path as ospath
    from sys import path as syspath
    parentdir = ospath.dirname(ospath.dirname(ospath.abspath(__file__)))
    syspath.insert(0, parentdir)
    from utils import io

"""Collects contact info from schools in India.

This is a pretty slow scraper because of the site's design, which makes it
difficult to scrape all the content quickly.

High-level algorithm:

    go to home page
    click on state search
    get list of states and their html values
    for every state in the list
        for every letter in the alphabet
            go to state search page and select current state
            search letter
            for every page of results
                for every school on current page
                    extract, parse, and clean data 

There is an option to specify a maximum time (in seconds) to wait between page
requests. This option is useful for randomizing the scraping patterns, which
makes it less obvious that the scraping is performed by a bot. It also reduces
the load on the server(s) by spreading out the requests over a longer period.

Examples:
    python scraper.py
    python scraper.py --help
    python scraper.py --version
    python scraper.py --log=info
    python scraper.py --log info
    python scraper.py --max-pause 5
    python scraper.py --append
    python scraper.py --unique
"""

region = 'india'  # Region/state/province/etc.

# This dictionary is to be used for the file output.
# Some database tables have a 2-character limit on a state/province column.
# Note that some of the names used by the school directory are outdated.
# Source: http://en.wikipedia.org/wiki/States_and_territories_of_India
state_codes = {
    'Andaman & Nicobar':'AN', 'Andhra Pradesh':'AP', 'Arunachal Pradesh':'AR',
    'Assam':'AS', 'Bihar':'BR', 'Chandigarh':'CH', 'Chattisgarh':'CT',
    'Dadar & Nagar Haveli':'DN', 'Daman & Diu':'DD', 'Delhi':'DL',
    'Foreign Schools':'??', 'Goa':'GA', 'Gujarat':'GJ', 'Haryana':'HR',
    'Himachal Pradesh':'HP', 'Jammu & Kashmir':'JK', 'Jharkhand':'JH',
    'Karnataka':'KA', 'Kerala':'KL', 'Lakshadweep':'LD', 'Madhya Pradesh':'MP',
    'Maharashtra':'MH', 'Manipur':'MN', 'Meghalaya':'ML', 'Mizoram':'MZ',
    'Nagaland':'NL', 'Orissa':'OR', 'Pondicherry':'PY', 'Punjab':'PB',
    'Rajasthan':'RJ', 'Sikkim':'SK', 'Tamilnadu':'TN', 'Tripura':'TR',
    'Uttar Pradesh':'UP', 'Uttaranchal':'UT', 'West Bengal':'WB'}

class Scraper(object):
    """A scraper that collects contact info of schools in India.

    Attributes:
    - base_url: URL of the website that contains the school directories.
    - seconds: Maximum amount of seconds to wait between page requests.
    - output: Output file path that will contain the extracted data.
    - states_and_values: Dictionary of states and their SELECT value.
    """

    def __init__(self, url, secs, out):
        """Inits Scraper with the proper URLs and an empty browser driver."""
        self.base_url = url
        self.seconds = secs
        self.output = out
        self._browser = None
        self.states_and_values = None
        self._current_state = None

    def scrape(self):
        """Scrapes website and extracts the contact info of all schools."""
        self._browser = webdriver.Chrome()
        self.states_and_values = self.__get_states_and_values()
        self.__iterate_states_and_search()
        self._browser.close()
            

    def __retry_until_element_found_by_id(self, element_id):
        """Returns the element if found, otherwise retries.

        Note that each retry is slower than the previous one.
        """
        secs = 1
        while True: # Safety measure in case page doesn't load.
            try:
                return self._browser.find_element_by_id(element_id)
            except NoSuchElementException:
                if self._browser.title == 'errmsg':
                    logging.warning("Servers are facing a temporary technical "
                                    "problem... Backing up and trying again.")
                    self._browser.back()
                    continue
                else:
                    logging.warning("Issue finding Next button. Waiting %s "
                                    "seconds before reloading the page and "
                                    "retrying.")
                    time.sleep(secs)
                    self._browser.refresh()
                    secs = math.ceil(secs * 1.8)
                    continue
            break # The page loaded fine, break.

    def __goto_state_search_and_select_state(self, value):
        """Goes to the "State wise" search and selects the given state."""
        self._browser.get(self.base_url)
        self._browser.find_element_by_id('optlist_2').click()
        Select(self._browser.find_element_by_id('ddlitem')).select_by_value(value)

    def __goto_state_search_and_get_state_list(self):
        """Goes to the "State wise" search and returns the State select element.

        From here you can search by state and keyword.
        """
        # (Re)visit the URL to reset page history. Otherwise a new search
        # will start from the old page number instead of the first results page.
        self._browser.get(self.base_url)
        assert 'AllView' in self._browser.title, 'Wrong webpage.'
        
        # Select the 'State' radiobox.
        self._browser.find_element_by_id('optlist_2').click()
        
        try:  # `Select` is more efficient than `find_elements_by_tag_name()`
            return Select(self._browser.find_element_by_id('ddlitem'))
        except UnexpectedTagNameException:
            logging.critical('ddlitem element is not a SELECT tag.')
        except StaleElementReferenceException:
            logging.critical('ddlitem element does not exist.')
   
    def __get_states_and_values(self):
        """Returns an ordered dictionary of states and their values.

        Data taken from the "Select A State" dropdown list.
        Dictionary sorted by state name (which is the key).
        This method should only be ran once.
        """
        state_list = self.__goto_state_search_and_get_state_list()
        states_and_values = {str(option.text).title().strip():
                             str(option.get_attribute('value')) for option in
                             state_list.options[1:]} # 1st option is junk.
        logging.info("Found %d states", len(states_and_values))
        return collections.OrderedDict(sorted(states_and_values.items()))

    def __iterate_states_and_search(self):
        """Iterates through all the states and performs a search on each."""

        for state, value in self.states_and_values.iteritems():
            logging.info("Scraping state %s", state)
            self._current_state = state
            """
            if state == 'Tamilnadu': # TODO remove after scraping complete
                for letter in 'tuvwxyz':
                    # Reset search, otherwise current search will start from
                    # the page number that the last search finished on.
                    self.__goto_state_search_and_select_state(value)
                    time.sleep(random.randint(0, self.seconds)) # Pause between letter searches.
                    self.__search_for(letter)
            else:
            """
            for letter in string.lowercase:
                # Reset search, otherwise current search will start from
                # the page number that the last search finished on.
                self.__goto_state_search_and_select_state(value)
                time.sleep(random.randint(0, self.seconds)) # Pause between letter searches.
                self.__search_for(letter)
        
    def __search_for(self, query):
        """Searches for the given query.
        
        Searching is done by state and then by keyword.
        The reason for searching by state is because the state information is
        sometimes left out from the address, so now we can get the state info.
        """

        # Find the search box, clear it, and enter the query text.
        search_box = self._browser.find_element_by_id('keytext')
        search_box.clear()
        search_box.send_keys(query)
        
        # Find the search submit button and click it.
        self._browser.find_element_by_id('search').click()
        logging.info("\tSearching for schools with '%s' in the name or address",
                     query)
        
        try:
            num_results = int(self._browser.find_element_by_id('tot').text)
            num_pages = math.ceil(num_results / 25.0)
            logging.info("\tFound %d %s (%d %s)", num_results,
                         "school" if num_results == 1 else "schools", num_pages,
                         "page" if num_pages == 1 else "pages")
        except NoSuchElementException:
            try:
                assert self._browser.find_element_by_id('label').text == 'No Record Found For This KeyWord', 'Unknown error'
                logging.info("\tFound 0 schools")
                return
            except NoSuchElementException:
                logging.warning("\tSearch failed, skipping this search")
                return

        self.__iterate_results(num_pages)

    def __iterate_results(self, num_pages):
        """Iterates through the pages of results and scrapes them.
        
        Stops when the Next button is disabled (i.e. on the last page).
        """
        for page_num in xrange(1, int(num_pages) + 1):
            time.sleep(random.randint(0, self.seconds)) # Pause between pages.
            logging.info("\t\tScraping page %d", page_num)
            self.__scrape_schools()
            next_button = self.__retry_until_element_found_by_id('Button1')
            assert 'next' in next_button.get_attribute('value').lower(), 'Found the wrong button.'
            if not next_button.is_enabled(): # Just to be safe.
                break
            next_button.click()

    def __scrape_schools(self):
        """Scrapes the contact info of the schools."""
        school_id = 'null'
        school_name = None
        address = None
        city = 'N/A'
        state = state_codes[self._current_state]
        postal_code = None
        schoolboard = 'null'
        contact_name = None
        phone = None  # http://en.wikipedia.org/wiki/Telephone_numbers_in_India
        contact_position = 'Principal'
        email = None
        timezone = 'Asia/Kolkata'
        country = 'IN'

        tables = self._browser.find_elements_by_xpath('//*[@id="T1"]/tbody/tr/td/table')
        for table in tables[1:]: # Skip first element, it's label junk.
            school_data = table.text.split('\n') # List of school data.
            # Example of school_data contents:
            # [0] 1
            # [1] Affiliation No.130297
            # [2] Name: Azaan International School
            # [3] Head/Principal Name:Mrs.Perween Sultana Shikoh
            # [4] Address: 9-4-136, Seven Tombs road, Tolichowki, Hyderabad ,500008
            # [5] Phone No:,04064509370,04024413483
            # [6] Email:azaan.cbse@gmail.com
            school_name = school_data[2].split(':')[1].strip().title().encode('ascii', 'ignore')
            email = school_data[6].split(':')[1].strip().lower()
            if not email:
                logging.debug('\t\t\tSkipped: %s\n\n', school_name)
                continue

            # Note that contact name may contain spacing issues.
            contact_name = school_data[3].split(':')[1].strip().title().encode('ascii', 'ignore')
            phone = school_data[5].split(':')[1].replace(' ', '').replace(',', ' ').strip()
            if not phone or phone.isspace():
                phone = 'null'
           
            # I thought about adding .replace(state, '') to remove the state
            # from the address, but some places have part of the state name as
            # a legitimate part of their address, like New Delhi in Delhi.
            full_address = school_data[4].split(':')[1].title().encode('ascii', 'ignore')
            address_list = re.split('(,[0-9]{6})', full_address) # Split by postal code.
            address = address_list[0].strip()
            if address.endswith(','):  # Remove trailing comma if exists.
                address = address[:-1]
            try:
                postal_code = address_list[1][1:]
            except IndexError:  # Some addresses do not contain a postal code.
                postal_code = 'N/A'
           
            # Because this file is constantly being opened and closed for every
            # entry, the filemode HAS to be append. If the performance suffers
            # too greatly, open the file before scraping and close it when
            # completed, though this will complicate error handling.
            with open(self.output, 'a') as csv_file:
                csv_file.write('{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n'.format(
                                school_id, school_name, address, city, state,
                                postal_code, schoolboard, contact_name, phone,
                                contact_position, email, timezone, country))

            logging.debug(('\t\t\tschool id = {}\n'
                           '\t\t\tschool name = {}\n'
                           '\t\t\taddress = {}\n'
                           '\t\t\tcity = {}\n'
                           '\t\t\tstate = {}\n'
                           '\t\t\tpostal code = {}\n'
                           '\t\t\tschoolboard = {}\n'
                           '\t\t\tcontact name = {}\n'
                           '\t\t\tcontact phone = {}\n'
                           '\t\t\tcontact position = {}\n'
                           '\t\t\tcontact email = {}\n'
                           '\t\t\ttimezone = {}\n'
                           '\t\t\tcountry = {}\n\n').format(
                               school_id, school_name, address, city, state,
                               postal_code, schoolboard, contact_name, phone,
                               contact_position, email, timezone, country))

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
        description='Scrape contact info from Indian schools.',
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
                        help='Specify the output filename (default: %(default)s.csv)')
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
    scraper = Scraper('http://164.100.50.30/SchoolDir/userview.aspx',
                      args.seconds, datapath)
    scraper.scrape()
    
    if args.unique:
        io.remove_dupes(datapath)

if __name__ == '__main__':
    main()
