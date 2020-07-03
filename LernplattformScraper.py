#!/usr/bin/env python3
import argparse
import json
import sys
import yaml

from mebis_scraper.scrapers import LernplattformScraper
from mebis_scraper.visitors import LernplattformFilterVisitor
from mebis_scraper.acceptors import (LernplattformCompositeAcceptor,
                                     LernplattformListerAcceptor,
                                     LernplattformDownloadAcceptor)
from selenium_scraping.auth import (AuthenticationManager,
                                    MebisSAMLAuthenticator)
from selenium_scraping.profiles import make_firefox_profile


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Lists the "Mebis Lernplattform" courses for some user.')

    parser.add_argument('-l', '--credentials-file',
                        type=argparse.FileType('r'),
                        default='mebis-credentials.json',
                        dest='credfile',
                        help=('JSON file where mebis-ls will get the user\'s'
                              'credentials from'))
    parser.add_argument('-c', '--scraper-config',
                        type=argparse.FileType('r'),
                        default='mebis-scraper-config.yml',
                        dest='config',
                        help=('YAML file from which the scraper will derive'
                              'which courses and subjects to visit.'))

    parser.add_argument('-L', '--action-list',
                        dest='action_list',
                        required=False,
                        action='store_true',
                        help='List activities and their courses to stdout')
    parser.add_argument('-D', '--action-download',
                        dest='action_download',
                        metavar='OUT',
                        required=False,
                        help='Download activities to OUT')

    args = parser.parse_args()

    if not (args.action_download or args.action_list):
        sys.exit('Specify at least either -D or -L')

    creds = json.load(args.credfile)
    config = yaml.safe_load(args.config)

    authm = AuthenticationManager()

    username = creds['username']
    password = creds['password']
    sauth = MebisSAMLAuthenticator(username, password)
    authm.add_authenticator(sauth)

    (dl_dir, driver) = make_firefox_profile()
    with LernplattformScraper.create(driver, authm) as scraper:
        acceptors = LernplattformCompositeAcceptor()

        lister = None
        if args.action_list:
            lister = LernplattformListerAcceptor()
            acceptors.add_acceptor(lister)

        if args.action_download is not None:
            downloader = LernplattformDownloadAcceptor(args.action_download,
                                                       dl_dir)
            acceptors.add_acceptor(downloader)

        mebis_filter = LernplattformFilterVisitor(acceptors, config)

        scraper.visit(mebis_filter)

        json.dump(lister.res, sys.stdout, indent=4)

    driver.quit()
