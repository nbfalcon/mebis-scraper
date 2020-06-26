#!/usr/bin/env python3

from http.client import HTTPSConnection
from bs4 import BeautifulSoup
import argparse
import json
import sys


class MebisScraper:

    lernplattform_url = 'lernplattform.mebis.bayern.de'

    def __init__(self, username, password):
        self.conn = HTTPSConnection(self.lernplattform_url)
        self.username = username
        self.password = password

    def list_lernplattform_courses(self):
        page = self._fetchpage()
        if MebisScraper._is_login(page):
            self._handle_login(page)

        page = self._fetchpage()
        assert (not MebisScraper._is_login(page))

        return MebisScraper.find_lernplattform_courses(page)

    def find_lernplattform_courses(page):
        soup = BeautifulSoup(page, 'html.parser')

        courses_raw = soup.find_all('span', {'class': 'coursename internal'})

        courses = map(lambda course: course.text, courses_raw)

        return courses

    def _fetchpage(self):
        self.conn.request("GET", "/")
        self.conn.getresponse().msg

    def _is_login(page):
        soup = BeautifulSoup(page, 'html.parser')


        return soup.title.string == 'Mebis Login Service'

    def _handle_login(self, page):
        soup = BeautifulSoup(page, 'html.parser')

        main_login_form = soup.find('form')

        login_target_path = main_login_form['action']

        self.conn.request('POST',
                          login_target_path + f'&j_username={self.username}&j_password={self.password}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lists the "Mebis Lernplattform" courses for some user.')

    parser.add_argument('-c', '--credentials-file',
                        nargs=1, type=argparse.FileType('r'),
                        default='mebis-credentials.json',
                        dest='credfile',
                        help='JSON file where mebis-ls will get the user\'s credentials from')

    args = parser.parse_args()

    creddb = args.credfile

    creds = json.load(creddb)

    username = creds['username']
    password = creds['password']

    scraper = MebisScraper(username, password)

    courses = scraper.list_lernplattform_courses()

    json.dump(courses, sys.stdout)
