#! /usr/bin/env python
# encoding: utf-8
"""

Usage:
  make_ga_collector_config.py --ga-id <ga-id>
                              [--target <backdrop-target>]
                              [--token <bearer-token>]

Options:
  -h --help     Show this screen
  -g --ga-id    8-digit GA query ID
  -T --target   Backdrop endpoint
  -t --token    Bearer token

"""

from __future__ import unicode_literals

import codecs
import collections
import csv
import errno
import json
import os
import sys

import docopt
import jinja

from collections import OrderedDict

TEMPLATE_GA_CONFIG = OrderedDict([
    ('dataType', None),
    ('query', {
        'id': None,
        'metrics': None,
        'dimensions': None,
        'filters': None}),
    ('idMapping', None),
    ('target', {'url': None, 'token': None})
])


def get_all_keys(d):
    all_keys = []
    for k, v in d.items():
        #new_key = parent_key + '_' + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            all_keys.append(k)
            all_keys.extend(get_all_keys(v))
        else:
            all_keys.append(k)
    return set(all_keys)


def make_expected_keys_from_template():
    flattened = get_all_keys(TEMPLATE_GA_CONFIG)
    return set(flattened)

EXPECTED_KEYS = make_expected_keys_from_template()


def read_ga_collector_config(filename):
    with open(filename, 'r') as f:
        ga_config = json.load(f)
    return ga_config


def validate_config(ga_config):
    test1, _ = has_all_expected_keys(ga_config)
    test2, _ = has_no_unexpected_keys(ga_config)
    return test1 and test2


def has_all_expected_keys(ga_config):
    result = True
    dict_keys = get_all_keys(ga_config)
    missing_keys = EXPECTED_KEYS.difference(dict_keys)
    if len(missing_keys) != 0:
        result = False
    return result, missing_keys


def has_no_unexpected_keys(ga_config):
    result = True
    dict_keys = get_all_keys(ga_config)
    unexpected_keys = dict_keys.difference(EXPECTED_KEYS)
    if len(unexpected_keys) != 0:
        result = False
    return result, unexpected_keys


def load_csv_as_json(path):
    """
    Read a csv file into json dictionaries, using the first row as keys
    """
    with open(path) as fd:
        rows = list(csv.reader(fd))

    headings = rows.pop(0)
    return [dict(zip(headings, values)) for values in rows]


def output_bucket_config(row):
    bucket_name = "{dataGroup}_{dataType}".format(**row).replace("-", "_")
    print("invoke create_bucket --rawqueries {bucket_name}"
          " {dataGroup} {dataType} "
          "--token=scraperwiki".format(
              bucket_name=bucket_name, **row))


def output_ga_collector_config(row, args):

    template = jinja.from_string(
        open("collector-config/ga-collector-template.json").read())

    def split(sep, what):
        if not what:
            return []

        def strip(x):
            x = x.strip()
            if x.startswith("ga:"):
                x = x[len("ga:"):]
            if x.startswith("-ga:"):
                x = "-" + x[len("-ga:"):]
            return x
        return [strip(x) for x in what.split(sep)]

    metrics = split(",", row["Metrics"])
    dimensions = split(",", row["Dimensions"])
    filters = split(";", row["Filters"])
    sort = split(";", row["Sort"])

    if not metrics:
        print "Skipping {} (no metrics)".format(row["dataType"])
        return

    row["ga_id"] = args["<ga-id>"]
    row["metrics"] = json.dumps(metrics)
    row["dimensions"] = json.dumps(dimensions)
    row["filters"] = json.dumps(filters)
    row["sort"] = json.dumps(sort)
    row["maxResults"] = row["maxResults"] or 0

    # Hardwired in template
    dimensions.remove("customVarValue9")

    row["id_params"] = ", ".join("'{}'".format(m) for m in dimensions)

    def agg(m):
        func = "aggregate_count"
        return "{}('{}')".format(func, m)

    row["aggregation_params"] = ", ".join(agg(m) for m in metrics)

    row["bearer_token"] = args["<bearer-token>"]
    row["backdrop_target"] = args["<backdrop-target>"]
    data_type = row['dataType'].replace("-", "_")
    row["bucket_name"] = "{}_{}".format(row['dataGroup'], data_type)

    try:
        os.makedirs("collector-config/output")
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Data type must be -'ified
    row["dataType"] = row["dataType"].replace("_", "-")

    path = "collector-config/output/{}.json".format(row["bucket_name"])
    with open(path, "w") as fd:
        fd.write(template.render(**row))


def output_spotlight_config(row, args):
    template = jinja.from_string(
        open("spotlight-config/content-dashboard-template.json").read())

    try:
        os.makedirs("spotlight-config/output")
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    fmt = "spotlight-config/output/{}.json"
    path = fmt.format(row["dashboard_config_name"])
    with open(path, "w") as fd:
        fd.write(template.render(**row))


def main(args):

    INPUT_CSV_PATH = "collector-config/GoogleAnalyticsQueries - Searches.csv"

    for row in load_csv_as_json(INPUT_CSV_PATH):
        output_bucket_config(row)
        output_ga_collector_config(row, args)

    # TODO(pwaller): Need to introduce this
    # departments = load_csv_as_json(INPUT_CSV_PATH)
    departments = [
        {
            "dashboard_config_name": "dft-content-dashboard",
            "dept_name": "Department for Transport",
            "dept_abbrev": "DFT",
            "dept_slug": "department-for-transport",
        },
        {
            "dashboard_config_name": "dfe-content-dashboard",
            "dept_name": "Department for Education",
            "dept_abbrev": "DFE",
            "dept_slug": "department-for-education",
        }
    ]

    for department in departments:
        output_spotlight_config(department, args)


if __name__ == '__main__':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    args = docopt.docopt(__doc__)
    main(args)

# References
# Dictionary Flattening:
# http://stackoverflow.com/questions/6027558/
#        flatten-nested-python-dictionaries-compressing-keys
