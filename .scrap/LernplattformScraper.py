#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import argparse
import json
import sys
import logging

class LernplattformScraper:

    lernplattform_url = 'https://lernplattform.mebis.bayern.de'
    idp_url = 'https://idp.mebis.bayern.de'

    def __init__(self, credentials):
        self.creds = credentials
        self.session = requests.Session()

    def _fetch_main_page(self):
        res = self.session.get(self.lernplattform_url + '/my/')

        return res.text

    def check_is_login_page(page):
        soup = BeautifulSoup(page, 'html.parser')

        with open('debug.isloginpage.txt', 'w') as f:
            f.write(soup.title.text)

        return soup.title.text == 'Mebis Login Service'

    def get_courses(self):
        page = self._fetch_main_page()
        if LernplattformScraper.check_is_login_page(page):
            self.creds.post_login(page, self.session)
            page = self._fetch_main_page()

        return LernplattformScraper.scrape_main_page(page)

    def scrape_main_page(page):
        soup = BeautifulSoup(page, 'html.parser')

        with open('debug.txt', 'w') as f:
            f.write(page)

        courses_raw = soup.find_all('span', {'class': 'coursename internal'})

        courses = list(map(lambda course: course.text, courses_raw))

        return courses

class LernplattformCredentials:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_login_table(self, page):
        soup = BeautifulSoup(page, 'html.parser')

        main_form = soup.find('form')

        main_form_inputs = main_form.find_all('input')

        login_form_table = {}

        for form_input in main_form_inputs:
            form_key = form_input['name']
            form_value = form_input.get('value')

            form_id = form_input.get('id')

            if form_id == 'username':
                form_value = self.username
            elif form_id == 'password':
                form_value = self.password

            login_form_table[form_key] = form_value


        post_target_base = LernplattformScraper.idp_url + main_form['action']
        with open('debug.form.json', 'w') as f:
            json.dump(login_form_table, f)

        return (post_target_base, login_form_table)

    def post_login(self, page, requests_session):
        (base, tbl) = self.get_login_table(page)

        res = requests_session.post(base, data=tbl)

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

    lpcreds = LernplattformCredentials(username, password)

    scraper = LernplattformScraper(lpcreds)

    courses = scraper.get_courses()

    json.dump(courses, sys.stdout)
