#!/usr/bin/env python
#
# Copyright 2013 Dennis Ideler

"""A module for common IO operations shared between the scraper modules.

Note that functions executed in this module will use the working directory that
script was executed from. For example, when using scraper.py, it will use its
directory.

TODO: Decide on where to keep the following functionality:
 - set_logger()
 - parse_args()
 - file output in extract_contact_info()
"""

import os

datapath = None
COUNTRIES = ('canada', 'india')

def data_dir_exists():
    """Creates the data directory if it doesn't exist and sets the path.

    This allows the scrapers to run correctly when run via scrapers.py
    or as standalone scripts in their own directories.
    """
    global datapath
    if os.path.isdir('./data'):
        datapath = './data/'
    elif os.path.isdir('../../data'):
        datapath = '../../data/'
    else:
        response = raw_input('No data directory exists. Create one [Y/n]? ')
        if not response or response[0].lower() == 'y':
            directory = os.getcwd()
            if os.path.basename(directory) == 'caribou-data-collection':
                datapath = './data/'
                os.mkdir(datapath)
                print 'Created', datapath
            elif os.path.basename(os.path.dirname(directory)) in COUNTRIES:
                datapath = '../../data/'
                os.mkdir(datapath)
                print 'Created', datapath
            else:
                raise RuntimeError('Directory not created. '
                                   'Please switch to the caribou-data-collection'
                                   ' directory and try again.')
        else:
            return False
    return True

def remove_dupes(infile):
    """Removes duplicate lines from the output file."""
    filename = infile.replace('.csv', '-unique.csv')
    s = set()
    with open(filename, 'w') as outfile:
        for line in open(infile):
            if line not in s:
                outfile.write(line)
                s.add(line)
