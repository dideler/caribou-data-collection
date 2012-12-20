# Does a simple Google search.
# http://code.google.com/p/chromedriver/wiki/GettingStarted

from selenium import webdriver

driver = webdriver.Chrome() # Optional argument; will search PATH if not specified.
driver.get('http://google.com/xhtml') # TODO: check if it works without xhtml
search_box = driver.find_element_by_name('q')
search_box.send_keys('ChromeDriver')
search_box.submit()
driver.quit()
