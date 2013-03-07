Collects the following contact information from publicly listed schools [1] in
India, and writes it to a comma-separated value file so it's easy to work with.

- school id = null
- school name
- school address
- city
- state
- postal code
- school board = null
- contact name
- contact phone number
- contact position
- contact email
- time zone
- country

```
usage: india_scraper.py [-h] [--log {debug,info,warning,error,critical}]
                        [--max-pause SECONDS] [-a] [-u] [-o OUTPUT] [-v]

Scrape contact info from Indian schools.

optional arguments:
  -h, --help            show this help message and exit
  --log {debug,info,warning,error,critical}
                        Log level (default: info)
  --max-pause SECONDS   Maximum amount of seconds to pause between page
                        requests (default: 0 sec)
  -a, --append          Append to the log file instead of overwriting it
  -u, --unique          Output file will contain unique data
  -o OUTPUT, --output OUTPUT
                        Specify the output filename (default: india.csv)
  -v, --version         show program's version number and exit

Happy scraping, use with care!
```

[1] Excluding post-secondary schools.
