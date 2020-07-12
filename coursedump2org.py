#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess

from bs4 import BeautifulSoup
from tools.flatten_coursedump import walk_json
from mebis_scraper.acceptors import LernplattformDownloadAcceptor


def pandoc_html_to_org(html):
    pandoc = subprocess.run(['pandoc', '--from', 'html', '--to', 'org'],
                            stdout=subprocess.PIPE,
                            input=html.encode('utf-8'))
    return pandoc.stdout.decode('utf-8')


def sanitize_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    soup.div.attrs = {}  # erase useless classes

    return soup.prettify()


class OrgBuilderVisitor:
    def __init__(self, dl_dir, workdir, out=sys.stdout):
        self.out = out
        self.dl_dir = dl_dir
        self.workdir = workdir

        self._dir_stack = []
        self._level = 1

    def enter_dict(self, obj):
        return True

    def exit_dict(self):
        pass

    def enter_kv(self, key):
        print('*'*self._level + f' {key}', file=self.out)
        self._level += 1

        self._dir_stack.append(key)

        return True

    def exit_kv(self):
        self._dir_stack.pop()
        self._level -= 1

    def enter_list(self, obj):
        self._level += 1

        for activity in obj:
            COMPLETE_TEXTS = {
                False: 'TODO',
                True: 'DONE'
            }

            complete = activity.get('complete', False) or False
            completed_time = activity.get('completed')
            name = activity['name']
            subtext = activity.get('subtext')
            activity_type = activity['type']

            ctext = COMPLETE_TEXTS[complete]
            course_wd = LernplattformDownloadAcceptor.make_path(
                self.workdir, *self._dir_stack, name)
            print('*'*self._level +
                  f' {ctext} [[file:{course_wd}/main.org][{name}]]',
                  file=self.out)

            content_file = LernplattformDownloadAcceptor.make_path(
                self.dl_dir, *self._dir_stack, name)
            real_content_file = LernplattformDownloadAcceptor \
                .find_activity(content_file)

            if completed_time is not None:
                print(f'CLOSED: {completed_time}', file=self.out)

            if real_content_file is not None:
                if activity_type in ['modtype_label', 'modtype_page',
                                     'modtype_url']:
                    with open(real_content_file, 'r') as content_file:
                        content = content_file.read()
                        if activity_type == 'modtype_url':
                            print(f'[[{content}][Link]]', file=self.out)
                        else:
                            self.out.write(pandoc_html_to_org(
                                sanitize_html(content)))
                else:
                    print(f'[[{real_content_file}][File]]', file=self.out)

            if subtext is not None:
                print('*'*(self._level + 1) + ' Note', file=self.out)
                self.out.write(pandoc_html_to_org(subtext))

        self._level -= 1
        return False

    def exit_list(self):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--download-dir', metavar='DOWNLOAD_DIRECTORY',
        dest='dl_dir',
        required=True,
        help='Directory where LernplattformScraper.py downloaded its files')
    parser.add_argument(
        '-w', '--workdir', metavar='WORKING_DIRECTORY',
        dest='workdir',
        required=True,
        help='Directory where the user will do the activities')
    parser.add_argument(
        'coursedump', metavar='coursedump',
        type=argparse.FileType('r'),
        help='Hierarchical course-dump from which to generate the org file')

    args = parser.parse_args()

    coursedump = json.load(args.coursedump)

    orgbuilder = OrgBuilderVisitor(args.dl_dir, args.workdir)
    walk_json(orgbuilder, coursedump)
