# yuma: yuma-ai(https://www.ai-yuma.com/) scraper
----------

### What is this?
----------
**yuma** is a python package for scraping yuma-ai(https://www.ai-yuma.com/) data.  

### Dependencies
----------
- [pandas](https://pandas.pydata.org/)
- [requests](https://requests-docs-ja.readthedocs.io/en/latest/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Usage
----------------------
To scrape yuma data.
```py
# import modules
import yuma

# scrape yuma data
# set 'JRA' or 'NAR' when generating instance from the Scraper class
jra_scraper = yuma.YumaScraper('JRA')
# specify the date in the form of yyyymmdd and scrape yuma data
# this function returns pandas DataFrame
scraper.scrape('20200829')
```
