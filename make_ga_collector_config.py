#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals

import codecs
import json
import sys
import collections
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


if __name__ == '__main__':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

# References
# Dictionary Flattening:
# http://stackoverflow.com/questions/6027558/
#        flatten-nested-python-dictionaries-compressing-keys
