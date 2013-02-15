#!/usr/bin/env python
#
# Copyright 2013 Dennis Ideler

"""A module for common IO operations shared between the scraper modules.

Note that functions executed in this module will use this module's current
working directory. Keep that in mind when importing this module.

TODO: Decide on where to keep the following functionality:
 - set_logger()
 - parse_args()
 - file output in extract_contact_info()
"""

import os

def pwd():
    """Print working directory."""
    return os.getcwd()

def create_data_dir():
    """Creates the data directory if it doesn't exist yet."""
    # TODO: Have it work when running an individual module as a script.
    # That is, not through scraper.py. Relative path will be different.
    if not os.path.exists('data'):
        os.mkdir('data')

def remove_dupes(infile):
    """Removes duplicate lines from the output file."""
    # TODO: Update location of input file (it should be in data/).
    # TODO: Create a datapath variable.
    s = set()
    with open("unique-" + infile, 'w') as outfile:
        for line in open(infile):
            if line not in s:
                outfile.write(line)
                s.add(line)
