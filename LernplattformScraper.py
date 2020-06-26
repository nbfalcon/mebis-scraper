#!/usr/bin/env python3
from selenium import webdriver

from selenium_auth.core import AuthenticationManager
from selenium_auth.authenticators import MebisSAMLAuthenticator

from mebis_scraper.scrapers import LernplattformScraper

import argparse
import json
import time
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lists the "Mebis Lernplattform" courses for some user.')

    parser.add_argument('-c', '--credentials-file',
                        type=argparse.FileType('r'),
                        default='mebis-credentials.json',
                        dest='credfile',
                        help='JSON file where mebis-ls will get the user\'s credentials from')
    args = parser.parse_args()

    authm = AuthenticationManager()

    creds = json.load(args.credfile)
    username = creds['username']
    password = creds['password']
    sauth = MebisSAMLAuthenticator(username, password)
    authm.add_authenticator(sauth)

    profile = webdriver.FirefoxProfile()
    profile.set_preference('general.useragent.override',
                           'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0')
    driver = webdriver.Firefox(profile)

    scraper = LernplattformScraper(driver, authm)

    # scraper.dump_page()
    json.dump(scraper.scrape_all(), sys.stdout)

    driver.quit()
