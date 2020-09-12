import datetime
import time
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

class YumaScrapere():
    def __init__(self, JRAorNAR):
        self.JRAorNAR = JRAorNAR

    def scrape(self, input_date):
        urls_getter = TargetRaceUrlsGetter(self.JRAorNAR)
        urls = urls_getter.get_urls(input_date)
        
        ret_df = pd.DataFrame([], columns=['date', 'course', 'race_number', 'horse_number', 'horse_name', 'yuma_index'])

        index_getter = YumaIndexGetter()
        for url in urls:
            add_df = index_getter.get_yuma_index(url)
            ret_df = pd.concat([ret_df, add_df])

        return ret_df

class TargetRaceUrlsGetter():
    PAGES_MAX = 100
    titles_page_url_fixed = 'https://www.ai-yuma.com/archive/'
    date_format = re.compile(r'^\d{8}')
    course_format = {
        'JRA': re.compile(r'(札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉)(\d{1,2})R'), 
        'NAR': re.compile(r'(門別|盛岡|水沢|浦和|船橋|大井|川崎|金沢|笠松|名古屋|園田|姫路|高知|佐賀|ばんえい)(\d{1,2})R')
                     }

    def __init__(self, JRAorNAR):
        self.JRAorNAR = JRAorNAR

    def get_urls(self, input_date):
        race_urls = []
        page_number = 1
        date_not_yet_appear_flag = True
        target_date = self._input_date_to_datetime(input_date)
        for i in range(self.PAGES_MAX):
            titles_page_url = self._get_titles_page_url(target_date, page_number)
            soup = self._get_page(titles_page_url)

            if self._check_existence_articles(soup):
                break

            dates_links_courses = self._get_dates_links_courses(soup)

            if self._check_target_date_not_in_page(target_date, dates_links_courses) and date_not_yet_appear_flag == True:
                page_number += 1
                continue
            elif self._check_target_date_not_in_page(target_date, dates_links_courses) and date_not_yet_appear_flag == False:
                break

            target_links = self._get_target_links(dates_links_courses, target_date)
            race_urls.extend(target_links)

            date_not_yet_appear_flag = False
            page_number += 1
        return race_urls

    def _input_date_to_datetime(self, input_date):
        target_date = datetime.datetime.strptime(input_date, '%Y%m%d').date()
        return target_date

    def _get_titles_page_url(self, target_date, page_number):
        titles_page_url = self.titles_page_url_fixed + str(target_date.year) + '/' + str(target_date.month) + '?page=' + str(page_number)
        return titles_page_url

    def _get_page(self, url):
        time.sleep(2)
        res = requests.get(url)
        #res.encoding = 'EUC-JP'
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup

    def _check_existence_articles(self, soup):
        if soup.find('div', id='main-inner').p.get_text() == '記事はありません':
            return True
        else:
            return False

    def _get_dates_links_courses(self, soup):
        title_atags = soup.find_all('a', class_='entry-title-link')
        dates_links_courses = [
                                (
                                    self._get_date_from_title_atag(title_atag), 
                                    self._get_link_from_title_atag(title_atag), 
                                    self._get_course_from_title_atag(title_atag)
                                ) for title_atag in title_atags
                               ]
        dates_links_courses = pd.DataFrame(dates_links_courses, columns=['date', 'link', 'course']).dropna().reset_index(drop=True)
        return dates_links_courses

    def _get_date_from_title_atag(self, title_atag):
        return datetime.datetime.strptime(self.date_format.search(title_atag.get_text()).group(), '%Y%m%d').date()

    def _get_link_from_title_atag(self, title_atag):
        return title_atag.get('href')

    def _get_course_from_title_atag(self, title_atag):
        try:
            return self.course_format[self.JRAorNAR].search(title_atag.get_text()).group(1)
        except:
            return None

    def _check_target_date_not_in_page(self, target_date, dates_links_courses):
        try:
            if target_date > dates_links_courses['date'][0] or target_date < dates_links_courses['date'][len(dates_links_courses)-1]:
                return True
        except KeyError:
            return True
        else:
            return False

    def _get_target_links(self, dates_links_courses, target_date):
        target_links = dates_links_courses[dates_links_courses['date']==target_date]['link']
        return target_links

class YumaIndexGetter():
    race_info_format = re.compile(r'^(\d{8}) (札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉|門別|盛岡|水沢|浦和|船橋|大井|川崎|金沢|笠松|名古屋|園田|姫路|高知|佐賀|ばんえい)(\d{1,2})R')
    number_name_index_format = re.compile(r'\d{1,2}【[\d/. ]+%】[\u30A1-\u30F4ー]+')
    number_name_index_split_format = re.compile(r'(\d{1,2})【([\d/. ]+)%】([\u30A1-\u30F4ー]+)')

    def __init__(self):
        pass

    def get_yuma_index(self, url):
        soup = self._get_page(url)
        print(self._get_title(soup))
        race_info = self._get_race_info(soup)
        table = self._get_table_data(soup)
        df = pd.DataFrame([[0 for i in range(6)] for j in range(len(table))], columns=['date', 'course', 'race_number', 'horse_number', 'horse_name', 'yuma_index'])
        df['date'] = race_info['date'][0]
        df['course'] = race_info['course'][0]
        df['race_number'] = race_info['race_number'][0]
        df[['horse_number', 'horse_name', 'yuma_index']] = table
        return df

    def _get_page(self, url):
        time.sleep(2)
        res = requests.get(url)
        #res.encoding = 'EUC-JP'
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup

    def _get_race_info(self, soup):
        title = self._get_title(soup)
        race_info = self._get_date_course_race_number(title)
        return race_info

    def _get_title(self, soup):
        title = soup.find('a', class_='entry-title-link bookmark').get_text()
        return title

    def _get_date_course_race_number(self, title):
        match_obj = self.race_info_format.search(title)
        date_course_race_number = pd.DataFrame([match_obj.group(1), match_obj.group(2), match_obj.group(3)]).T
        date_course_race_number.columns = ['date', 'course', 'race_number']
        return date_course_race_number

    def _get_table_data(self, soup):
        contents = self._get_contents(soup)
        number_name_index = self._get_number_name_index(contents)
        number_name_index_df = self._split_number_name_index(number_name_index)
        return number_name_index_df

    def _get_contents(self, soup):
        contents = soup.find('div', class_='entry-content').p.get_text()
        return contents

    def _get_number_name_index(self, contents):
        number_name_index = re.findall(number_name_index_format, contents)
        return number_name_index

    def _split_number_name_index(self, number_name_index):
        match_objs = [self.number_name_index_split_format.search(text) for text in number_name_index]
        number_name_index = [[int(match_obj.group(1)), match_obj.group(3), float(match_obj.group(2))] for match_obj in match_objs]
        number_name_index_df = pd.DataFrame(number_name_index, columns=['horse_number', 'horse_name', 'yuma_index']).sort_values('horse_number').reset_index(drop=True)
        return number_name_index_df
