#!/usr/bin/env python3
import argparse
import json
import sys


def locate_activity(overlay, course, subcourse, subject, name):
    if subcourse is not None:
        return overlay[course][subcourse][subject][name]
    else:
        return overlay[course][subject][name]


def patch_with_overlay(activities, overlay):
    # we reached the activities; patch them now
    for activity in activities:
        name = activity['name']
        subject = activity['subject']
        course = activity['course']
        subcourse = activity.get('subcourse')

        try:
            completed = locate_activity(overlay, course, subcourse,
                                        subject, name)
        except KeyError:
            pass  # Nothing to patch with
        else:
            activity['completed'] = completed.get('completed')
            activity['complete'] = completed.get('complete')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('overlay', type=argparse.FileType('r'), nargs='?',
                        help='Completion overlay to patch with')
    parser.add_argument('base', type=argparse.FileType('r'), nargs='?',
                        default=sys.stdin,
                        help='Course-dump (flat or hierarchical) to patch')

    args = parser.parse_args()

    base = json.load(args.base)
    patch_with_overlay(base, json.load(args.overlay))
    json.dump(base, sys.stdout, indent=4)
