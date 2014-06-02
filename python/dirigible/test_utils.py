# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from os.path import dirname, join
import sys

import django


def create_suite_for_file_directory(file):
    def suite():
        start_dir = dirname(file)
        return unittest.defaultTestLoader.discover(
            start_dir,
            top_level_dir=join(dirname(__file__), "..")
        )
    return suite


def die(exception=None):
    if exception is None:
        exception = AssertionError('die called')
    def inner_die(*_):
        raise exception
    return inner_die



class ResolverTestMixins(object):
    def assertCalledOnce(self, mock, *args, **kwargs):
        if mock.call_args_list == []:
            self.fail('Not called')
        self.assertEquals(mock.call_args_list, [(args, kwargs)])



class ResolverTestCase(unittest.TestCase, ResolverTestMixins):
    maxDiff = None



class ResolverDjangoTestCase(django.test.TestCase, ResolverTestMixins):
    maxDiff = None



TEST_CLASSES = (
    unittest.TestCase,
    django.test.TestCase,
    ResolverTestCase,
    ResolverDjangoTestCase
)

def assert_security_classes_exist(test, module_name, excludes=None):
    '''
    ensure that, as a minimum sanity check, each non-security test class in
    this module has an associated security test class.
    '''
    test_classes = [
        name for name, item in sys.modules[module_name].__dict__.iteritems()
        if isinstance(item, type) and issubclass(item, TEST_CLASSES)
        and not item in TEST_CLASSES
    ]
    regular_test_classes = [
        name for name in test_classes
        if not name.endswith('SecurityTest')
    ]
    if excludes is None:
        excludes = []
    for name in regular_test_classes:
        if name not in excludes:
            test.assertTrue(
                name[:-4] + 'SecurityTest' in test_classes,
                "class %s doesn't have a security test. "
                "Use user page security test as template" % (name,)
            )

