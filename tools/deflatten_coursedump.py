#!/usr/bin/env python3
import argparse
import json
import sys


def deflatten_coursedump(coursedump):
    result = {}
    for activity in coursedump:
        course = activity['course']
        subj = activity['subject']
        subcourse = activity.get('subcourse')

        if subcourse is not None:
            result.setdefault(course, {}) \
                  .setdefault(subcourse, {}) \
                  .setdefault(subj, []) \
                  .append(activity)
        else:
            result.setdefault(course, {}) \
                  .setdefault(subj, []) \
                  .append(activity)

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('coursedump', type=argparse.FileType('r'), nargs='?',
                        default=sys.stdin)

    args = parser.parse_args()

    coursedump = json.load(args.coursedump)

    json.dump(deflatten_coursedump(coursedump), sys.stdout, indent=4)
