#!/usr/bin/env python3
import argparse
import sys
import json


def coursedump_to_completion_overlay(activities):
    result = {}
    for activity in activities:
        course = activity['course']
        subcourse = activity.get('subcourse')
        subject = activity['subject']
        name = activity['name']

        if subcourse is not None:
            result.setdefault(course, {}) \
                  .setdefault(subcourse, {}) \
                  .setdefault(subject, {})[name] = activity
        else:
            result.setdefault(course, {}) \
                  .setdefault(subject, {})[name] = activity

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('coursedump', type=argparse.FileType('r'), nargs='?',
                        help='(flat) coursedump to be converted',
                        default=sys.stdin)

    args = parser.parse_args()

    json.dump(coursedump_to_completion_overlay(json.load(args.coursedump)),
              sys.stdout, indent=4)
