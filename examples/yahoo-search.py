# A simple Yahoo search. Slightly more complex than Google search example.
# http://selenium.googlecode.com/svn/trunk/docs/api/py/index.html

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time

browser = webdriver.Chrome() # Firefox is used in the original example.
browser.get('http://yahoo.com')
assert 'Yahoo!' in browser.title
query_box = browser.find_element_by_name('p')
query_box.send_keys('seleniumhq' + Keys.RETURN) # Note that the Enter key is hit.
time.sleep(0.2) # Selenium API doesn't support waiting for page loads yet...
                # However, ChromeDriver waits until the page is fully loaded
                # before returning, so I shouldn't have to use the time module.
try:
    browser.find_element_by_xpath("//a[contains(@href,'http://seleniumhq.org')]")
except:
    assert 0, "Cannot find seleniumhq"
browser.close()
