#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sys
import tempfile
import logging

import yaml
from selenium import webdriver

from mebis_scraper.scrapers import LernplattformScraper
from mebis_scraper.exceptions import UnsupportedActivityException
from selenium_auth.authenticators import MebisSAMLAuthenticator
from selenium_auth.core import AuthenticationManager


class LernplattformFilterVisitor(LernplattformScraper.Visitor):
    def __init__(self, acceptor, filter_dict):
        self.acceptor = acceptor
        self.filter = filter_dict
        self.current_course = None
        self.current_subcourse = None
        self.current_subject = None

        self.current_subject_filter = None

    def enter_course(self, name):
        # print(name)
        if name in self.filter:
            self.current_course = name
            return True

        return False

    def exit_course(self):
        self.current_course = None

    def enter_subcourse(self, name):
        # print(f'enter sc: {name}')
        if name in self.filter[self.current_course]['subcourses']:
            self.current_subcourse = name
            return True

        return False

    def exit_subcourse(self):
        # print(f'exit sc: {self.current_subcourse}')
        self.current_subcourse = None

    def enter_subject(self, name):
        # print(self.filter[self.current_course])
        # print(self.current_subcourse)
        nfilter = None
        if self.current_subcourse is not None:
            nfilter = (self.filter[self.current_course]
                       ['subcourses'][self.current_subcourse]
                       ['subjects'])
        else:
            nfilter = self.filter[self.current_course]['subjects']

        if name in nfilter:
            self.current_subject = name
            return True

        return False

    def exit_subject(self):
        self.current_subject = None

    def accept_activity(self, activity, auth, driver):
        self.acceptor.accept_activity(
            self.current_course, self.current_subcourse,
            self.current_subject,
            activity, auth, driver)


class LernplattformListerAcceptor:
    def __init__(self):
        self.res = {}

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        name = activity.get_name()

        if subcourse is None:
            self.res \
                .setdefault(course, {}) \
                .setdefault(subj, []).append(name)
        else:
            self.res \
                .setdefault(course, {}) \
                .setdefault(subcourse, {}) \
                .setdefault(subj, []).append(name)


class LernplattformDownloadAcceptor:
    def __init__(self, path, driver_download_dir):
        self.path = path
        self.dl_dir = driver_download_dir

    def make_path(self, *args):
        def escape_filename(filename):
            return filename.replace('/', '_')

        newpath = self.path

        for filename in args:
            if filename is not None:
                newpath = os.path.join(newpath, escape_filename(filename))

        return newpath

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        activity_name = activity.get_name()
        activity_type = activity.get_type()
        target_file = self.make_path(course, subcourse, subj, activity_name)

        if not os.path.exists(target_file):
            try:
                res = activity.download(driver, auth)
            except UnsupportedActivityException:
                logging.warning(f'Cannot download activity {activity_name}: '
                                f'its type ({activity_type}) '
                                'is unsupported.')
                return

            os.makedirs(os.path.dirname(target_file))

            if res is None:
                download_file = os.listdir(self.dl_dir)[0]
                shutil.move(download_file, target_file)
            else:
                with open(target_file, 'w') as out:
                    out.write(res)

            logging.info(f'Downloaded activity \'{activity_name}\''
                         '({activity_type})')


class LernplattformCompositeAcceptor:
    def __init__(self, acceptors=[]):
        self.acceptors = acceptors

    def add_acceptor(self, acceptor):
        self.acceptors.append(acceptor)

    def accept_activity(self, course, subcourse, subj, activity, auth, driver):
        for acceptor in self.acceptors:
            acceptor.accept_activity(course, subcourse, subj,
                                     activity, auth, driver)


def make_firefox_profile():
    AUTODOWNLOAD_MIMETYPES = [
        "audio/aac",
        "application/x-abiword",
        "application/x-freearc",
        "video/x-msvideo",
        "application/vnd.amazon.ebook",
        "application/octet-stream",
        "image/bmp",
        "application/x-bzip",
        "application/x-bzip2",
        "application/x-csh",
        "text/css",
        "text/csv",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # noqa: E501
        "application/vnd.ms-fontobject",
        "application/epub+zip",
        "application/gzip",
        "image/gif",
        "image/vnd.microsoft.icon",
        "text/calendar",
        "application/java-archive",
        "image/jpeg",
        "application/json",
        "application/ld+json",
        "text/javascript",
        "audio/mpeg",
        "video/mpeg",
        "application/vnd.apple.installer+xml",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.text",
        "audio/ogg",
        "video/ogg",
        "application/ogg",
        "audio/opus",
        "font/otf",
        "image/png",
        "application/pdf",
        "application/x-httpd-php",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # noqa: E501
        "application/vnd.rar",
        "application/rtf",
        "application/x-sh",
        "image/svg+xml",
        "application/x-shockwave-flash",
        "application/x-tar",
        "image/tiff",
        "video/mp2t",
        "font/ttf",
        "text/plain",
        "application/vnd.visio",
        "audio/wav",
        "audio/webm",
        "video/webm",
        "image/webp",
        "font/woff",
        "font/woff2",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.mozilla.xul+xml",
        "application/zip",
        "application/x-7z-compressed"
    ]
    AUTODOWNLOAD_MIMETYPES_CSV = ','.join(AUTODOWNLOAD_MIMETYPES)
    USERAGENT = ("Mozilla/5.0"
                 " (Windows NT 10.0; Win64; x64; rv:77.0)"
                 " Gecko/20100101 Firefox/77.0")

    dl_dir = tempfile.mkdtemp()

    prefs = {
        'general.useragent.override': USERAGENT,

        'browser.download.folderList': 2,
        'browser.download.manager.showWhenStarting': False,
        'browser.helperApps.alwaysAsk.force': False,
        'browser.helperApps.neverAsk.saveToDisk': AUTODOWNLOAD_MIMETYPES_CSV,

        'browser.download.manager.closeWhenDone': False,
        'browser.download.manager.focusWhenStarting': False,

        'browser.download.dir': dl_dir,
    }

    profile = webdriver.FirefoxProfile()
    for (pref, value) in prefs.items():
        profile.set_preference(pref, value)

    return (dl_dir, webdriver.Firefox(profile))


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
