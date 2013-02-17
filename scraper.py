#!/usr/bin/env python
#
# Copyright 2013 Dennis Ideler

# For now, import the specific modules directly.
# In the future when more scrapers exist, consider importing
# each country's __init__.py file.
# For example:
#   import canada # access the contents of canada/__init__.py
#   import usa
#   import india
#   ...etc.
from canada.britishcolumbia import bc_scraper

# TODO: Give example of commands.

bc_scraper.main()
