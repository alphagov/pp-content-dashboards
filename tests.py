#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
import unittest
from nose.tools import assert_equal
from os.path import join, dirname, abspath

from make_ga_collector_config import (read_ga_collector_config, EXPECTED_KEYS,
                                      has_all_expected_keys, has_no_unexpected_keys,
                                      validate_config)

SAMPLE_DIR = join(dirname(abspath(__file__)), 'examples/collector-config')

class GAConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = join(SAMPLE_DIR, 'gov_uk_most_viewed.json')
        cls.ga_config = read_ga_collector_config(filename)
    
    def test_make_expected_keys_from_template(self):
        assert_equal(10, len(EXPECTED_KEYS))


    def test_for_unexpected_keys(self):
        test_dict = {'id': None, 'bogus': None}
        test, unexpected_keys = has_no_unexpected_keys(test_dict)
        assert_equal(set(['bogus']), unexpected_keys)
        assert_equal(False, test)

    def test_for_missing_keys(self):
        test_dict = {u'dimensions': None,
                     u'dataType': None,
                     u'metrics': None,
                     u'url':None,
                     u'token':None,
                     u'filters':None,
                     u'idMapping':None,
                     u'target':None}

        test, missing_keys = has_all_expected_keys(test_dict)
        assert_equal(set(['id', 'query']), missing_keys)
        assert_equal(False, test)

    def test_validate_config(self):
        assert_equal(True, validate_config(self.ga_config))