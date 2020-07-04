#!/usr/bin/env python3
import argparse
import json
import sys
import yaml

from mebis_scraper.scrapers import LernplattformScraper
from mebis_scraper.visitors import LernplattformFilterVisitor
from mebis_scraper.acceptors import (LernplattformCompositeAcceptor,
                                     LernplattformListerAcceptor,
                                     LernplattformFlatListerAcceptor,
                                     LernplattformDownloadAcceptor,
                                     LernplattformCompletionFilterAcceptor,
                                     LernplattformCompletionSyncAcceptor)
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
    parser.add_argument('-u', '--download-incomplete',
                        action='store_true',
                        dest='dl_incomplete',
                        help='Download only incomplete activities')
    parser.add_argument('-f', '--list-flat',
                        action='store_true',
                        dest='list_flat',
                        help='List activities in the flat format')

    parser.add_argument('-L', '--action-list',
                        dest='action_list',
                        action='store_true',
                        required=False,
                        help='List activities and their courses to stdout')
    parser.add_argument('-D', '--action-download',
                        dest='action_download',
                        metavar='OUT',
                        required=False,
                        help='Download activities to OUT')
    parser.add_argument('-S', '--action-sync-complete',
                        dest='action_sync',
                        type=argparse.FileType('r'),
                        required=False,
                        help='Set completeness status of activities from file')

    args = parser.parse_args()

    if not (args.action_download or args.action_list or args.action_sync):
        sys.exit('Specify at least either -D, -L or -S')

    creds = json.load(args.credfile)
    config = yaml.safe_load(args.config)

    authm = AuthenticationManager()

    username = creds['username']
    password = creds['password']
    sauth = MebisSAMLAuthenticator(username, password)
    authm.add_authenticator(sauth)

    (dl_dir, _driver) = make_firefox_profile()
    with _driver as driver, \
         LernplattformScraper.create(driver, authm) as scraper:
        acceptors = LernplattformCompositeAcceptor()

        lister = None
        if args.action_list:
            lister = (LernplattformFlatListerAcceptor() if args.list_flat
                      else LernplattformListerAcceptor())
            acceptors.add_acceptor(lister)

        if args.action_download is not None:
            downloader = LernplattformDownloadAcceptor(
                args.action_download, dl_dir)
            if args.dl_incomplete:
                fdownloader = LernplattformCompletionFilterAcceptor(
                    downloader)
                acceptors.add_acceptor(fdownloader)
            else:
                acceptors.add_acceptor(downloader)

        if args.action_sync is not None:
            cdict = json.load(args.action_sync)
            completer = LernplattformCompletionSyncAcceptor(cdict)
            acceptors.add_acceptor(completer)

        mebis_filter = LernplattformFilterVisitor(acceptors, config)

        scraper.visit(mebis_filter)

        if args.action_list:
            json.dump(lister.result, sys.stdout, indent=4)
