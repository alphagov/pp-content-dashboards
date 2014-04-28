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


def make_bool(what):
    if not what or not isinstance(what, basestring):
        return False
    if what.lower() in ("yes", "on", "1", "true", "separate"):
        return True
    return False


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

    if sort == ["date"]:
        sort = []

    def fix_filter(f):
        if "{{departments}}" not in f:
            return f

        DEPARTMENTS = ("D1|D2|D3|D4|D5|D6|D7|D8|D9|D10|D11|D12|D13|D14|D15|D16"
                       "|D17|D18|D19|D23|D24|D25|EA74|EA75|EA79|OT532|OT537")
        return f.replace("{{departments}}", "<({})>".format(DEPARTMENTS))

    filters = [fix_filter(f) for f in filters]

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
    if "customVarValue9" in dimensions:
        dimensions.remove("customVarValue9")

    row["id_params"] = ", ".join("'{}'".format(m) for m in dimensions)

    def agg(m):
        func = "aggregate_count"
        return "{}('{}')".format(func, m)

    row["aggregation_params"] = ", ".join(agg(m) for m in metrics)

    row["bearer_token"] = args["<bearer-token>"]
    row["backdrop_target"] = args["<backdrop-target>"]

    fmt = "{dataGroup}_{dataType}"
    row["bucket_name"] = fmt.format(**row).replace("-", "_")

    # If we need to have many filtersets
    row["separateQueries"] = make_bool(row.get("separateQueries"))

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

    if "feedback_abbrev" not in row:
        row["feedback_abbrev"] = row["dept_abbrev"].lower()

    fmt = "spotlight-config/output/site-activity-{dept_slug}.json"
    path = fmt.format(**row)
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
            "dept_abbrev": "AGO",
            "dept_slug":  "attorney-generals-office",
            "dept_name": "Attorney General's Office",
        },
        {
            "dept_abbrev": "BIS",
            "dept_slug":  "department-for-business-innovation-skills",
            "dept_name": "Department for Business, Innovation & Skills"
        },
        {
            "dept_abbrev": "CO",
            "dept_slug": "cabinet-office",
            "dept_name": "Cabinet Office",
        },
        {
            "dept_abbrev": "DCLG",
            "dept_slug": "department-for-communities-and-local-government",
            "dept_name": "Department for Communities and Local Government",
        },
        {
            "dept_abbrev": "DCMS",
            "dept_slug": "department-for-culture-media-sport",
            "dept_name": "Department for Culture, Media & Sport",
        },
        {
            "dept_abbrev": "DfE",
            "dept_slug": "department-for-education",
            "dept_name": "Department for Education",
        },
        {
            "dept_abbrev": "Defra",
            "dept_slug": "department-for-environment-food-rural-affairs",
            "dept_name": "Department for Environment, Food & Rural Affairs",
        },
        {
            "dept_abbrev": "DFID",
            "dept_slug": "department-for-international-development",
            "dept_name": "Department for International Development",
        },
        {
            "dept_abbrev": "DFT",
            "dept_slug": "department-for-transport",
            "dept_name": "Department for Transport",
        },
        {
            "dept_abbrev": "DWP",
            "dept_slug": "department-for-work-pensions",
            "dept_name": "Department for Work and Pensions",
        },
        {
            "dept_abbrev": "DECC",
            "dept_slug": "department-of-energy-climate-change",
            "dept_name": "Department of Energy & Climate Change",
        },
        {
            "dept_abbrev": "DH",
            "dept_slug": "department-of-health",
            "dept_name": "Department of Health",
        },
        {
            "dept_abbrev": "FCO",
            "dept_slug": "foreign-commonwealth-office",
            "dept_name": "Foreign & Commonwealth Office",
        },
        {
            "dept_abbrev": "HMT",
            "dept_slug": "hm-treasury",
            "dept_name": "HM Treasury",
        },
        {
            "dept_abbrev": "HO",
            "dept_slug": "home-office",
            "dept_name": "Home Office",
            "feedback_abbrev": "home_office",
        },
        {
            "dept_abbrev": "MOD",
            "dept_slug": "ministry-of-defence",
            "dept_name": "Ministry of Defence",
        },
        {
            "dept_abbrev": "MOJ",
            "dept_slug": "ministry-of-justice",
            "dept_name": "Ministry of Justice",
        },
        {
            "dept_abbrev": "NIO",
            "dept_slug": "northern-ireland-office",
            "dept_name": "Northern Ireland Office",
        },
        {
            "dept_abbrev": "SO",
            "dept_slug": "scotland-office",
            "dept_name": "Scotland Office",
            "feedback_abbrev": "scotland_office",
        },
        {
            "dept_abbrev": "WO",
            "dept_slug": "wales-office",
            "dept_name": "Wales Office",
        },
        {
            "dept_abbrev": "HMRC",
            "dept_slug": "hm-revenue-customs",
            "dept_name": "HM Revenue & Customs",
        },
        {
            "dept_abbrev": "DVLA",
            "dept_slug": "driver-and-vehicle-licensing-agency",
            "dept_name": "Driver & Vehicle Licensing Agency",
        },
        {
            "dept_abbrev": "DSA",
            "dept_slug": "driving-standards-agency",
            "dept_name": "Driving Standards Agency",
        },
        {
            "dept_abbrev": "VOSA",
            "dept_slug": "vehicle-and-operator-services-agency",
            "dept_name": "Vehicle & Operator  Services Agency",
        },
        {
            "dept_abbrev": "No 10",
            "dept_slug": "prime-ministers-office-10-downing-street",
            "dept_name": "Prime Minister's Office, 10 Downing Street",
            "feedback_abbrev": "number_10",
        },
        {
            "dept_abbrev": "ODPM",
            "dept_slug": "deputy-prime-ministers-office",
            "dept_name": "The Deputy Prime Minister's Office",
            "feedback_abbrev": "dpmo",
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
