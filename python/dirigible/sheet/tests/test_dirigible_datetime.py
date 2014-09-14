# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import datetime
from sheet.dirigible_datetime import DateTime
from test_utils import ResolverTestCase

class DateTimeTest(ResolverTestCase):

    def test_DateTime_subclasses_datetime_dot_datetime(self):
        self.assertTrue(isinstance(
            DateTime(1979, 10, 8),
            datetime.datetime))
