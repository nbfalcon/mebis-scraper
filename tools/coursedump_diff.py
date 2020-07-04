#!/usr/bin/env python3
import sys
import json


def activity_to_locator_tuple(activity):
    course = activity['course']
    subcourse = activity.get('subcourse')
    subject = activity['subject']
    name = activity['name']

    return (course, subcourse, subject, name)


def activity_to_dict_tuple(activity):
    return (activity_to_locator_tuple(activity), activity)


def activity_list_to_dict(activities):
    return dict(map(activity_to_dict_tuple, activities))


def activity_dict_subtract(activities_b, activities_a):
    return [v for k, v in activities_b.items() if k not in activities_a]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'{sys.argv[0]}: usage: {sys.argv[0]} [b] [a]', file=sys.stderr)

    with open(sys.argv[1], 'r') as b_file, open(sys.argv[2]) as a_file:
        b = json.load(b_file)
        a = json.load(a_file)

        res = list(activity_dict_subtract(activity_list_to_dict(b),
                                          activity_list_to_dict(a)))

        json.dump(res, sys.stdout)
