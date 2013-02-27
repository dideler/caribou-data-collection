#!/usr/bin/env python
#
# Copyright 2013 Dennis Ideler

"""A module for common IO operations shared between the scraper modules.

Note that functions executed in this module will use the working directory that
script was executed from. For example, when using scraper.py, it will use its
directory.

TODO: Long term we should also move the following function to utils:
 - set_logger()
 - parse_args()
 - file output in extract_contact_info()?
"""

import os

datapath = None
COUNTRIES = ('canada', 'india')

def dir_exists(dirname):
    """Creates the specified directory if it doesn't exist and sets the path.

    This allows the scrapers to run correctly when run via scrapers.py
    or as standalone scripts in their own directories.
    """
    global datapath
    current_dir = './' + dirname + '/'
    parent_dir = '../' + dirname + '/'
    grandparent_dir = '../../' + dirname + '/'
    if os.path.isdir(current_dir):
        datapath = current_dir
    elif os.path.isdir(parent_dir):
        datapath = parent_dir
    elif os.path.isdir(grandparent_dir):
        datapath = grandparent_dir
    else:
        response = raw_input("'{}' directory does not exist. "
                             "Create it [Y/n]? ".format(dirname))
        if not response or response[0].lower() == 'y':
            directory = os.getcwd()
            if os.path.basename(directory) == 'caribou-data-collection':
                # E.g. /caribou-data-collection/scraper.py
                datapath = current_dir
                os.mkdir(datapath)
                print 'Created', datapath
            elif os.path.basename(directory) in COUNTRIES:
                # E.g. /caribou-data-collection/country/scraper.py
                datapath = parent_dir
                os.mkdir(datapath)
                print 'Created', datapath
            elif os.path.basename(os.path.dirname(directory)) in COUNTRIES:
                # E.g. /caribou-data-collection/country/region/scraper.py
                datapath = grandparent_dir
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
