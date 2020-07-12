#!/usr/bin/env python3
import json
import sys
import logging
import argparse


def walk_json(visitor, obj):
    if isinstance(obj, dict):
        if visitor.enter_dict(obj):
            for (key, value) in obj.items():
                if visitor.enter_kv(key):
                    walk_json(visitor, value)
                    visitor.exit_kv()
            visitor.exit_dict()
    elif isinstance(obj, list):
        if visitor.enter_list(obj):
            for sobj in obj:
                walk_json(visitor, obj)
            visitor.exit_list()
    else:
        visitor.accept_atom(obj)


class ActivityTupleBuilderVisitor:
    def __init__(self):
        self.result = []
        self._stack = []

    def enter_dict(self, obj):
        # (course, subcourse?, subject)
        if len(self._stack) >= 3:
            logging.getLogger('coursedump schema') \
                   .warning('Visitor course-dump too deep')
            return False

        self._stack.append(None)
        return True

    def exit_dict(self):
        self._stack.pop()

    def enter_kv(self, key):
        self._stack[-1] = key
        return True

    def exit_kv(self):
        pass

    def enter_list(self, obj):
        if len(self._stack) in [2, 3]:
            for activity in obj:
                self._accept_activity(activity)
        else:
            logging.getLogger('coursedump schema') \
                   .warning('Course-dump depth incorrect')

        return False

    def exit_list(self):
        pass

    def _accept_activity(self, activity):
        if not isinstance(activity, dict):
            logging.getLogger('coursedump schema') \
                .warning('Activities must be dicts')
            return

        course = self._stack[0]
        subcourse = self._stack[1] if len(self._stack) == 3 else None
        subject = self._stack[2] if len(self._stack) == 3 else self._stack[1]

        activity['course'] = course
        activity['subcourse'] = subcourse
        activity['subject'] = subject

        self.result.append(activity)

    def accept_atom(self, _):
        logging.getLogger('coursedump schema') \
               .warning('Illegal bare atom')


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    parser = argparse.ArgumentParser()

    parser.add_argument('coursedump', type=argparse.FileType('r'), nargs='?',
                        default=sys.stdin)

    args = parser.parse_args()

    coursedump = json.load(args.coursedump)
    visitor = ActivityTupleBuilderVisitor()

    walk_json(visitor, coursedump)

    json.dump(visitor.result, sys.stdout, indent=4)
