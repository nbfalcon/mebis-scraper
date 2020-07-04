#!/usr/bin/env python3
import json
import sys
import logging


logging.basicConfig(level='INFO')


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
            logging.warning('Schema error: visitor course-dump too deep')
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
            logging.warning(
                'Schema error: course-dump depth incorrect')

        return False

    def exit_list(self):
        pass

    def _accept_activity(self, activity):
        if not isinstance(activity, dict):
            logging.warning('Schema error: activities must be dicts')
            return

        course = self._stack[0]
        subcourse = self._stack[1] if len(self._stack) == 3 else None
        subject = self._stack[2] if len(self._stack) == 3 else self._stack[1]

        activity['course'] = course
        activity['subcourse'] = subcourse
        activity['subject'] = subject

        self.result.append(activity)

    def accept_atom(self, _):
        logging.warning('Schema error: illegal bare atom')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'{sys.argv[0]}: usage: {sys.argv[0]} [file]', file=sys.stderr)
        exit(1)

    with open(sys.argv[1], 'r') as input_file:
        coursedump = json.load(input_file)
        visitor = ActivityTupleBuilderVisitor()

        walk_json(visitor, coursedump)

        json.dump(visitor.result, sys.stdout, indent=4)
