# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import re
from functionaltest import FunctionalTest

class Test_2642_RecalcTimesInConsole(FunctionalTest):

    def test_recalc_time_appears_in_console(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some usercode
        self.append_usercode('worksheet[1, 1].value = 10')

        # * He notes that the console tells him how long the recalc took
        self.wait_for_cell_value(1, 1, '10')
        output = self.get_console_content()
        recalc_time_report_re = re.compile('Took \d+\.\d\d+s')
        found_time_report = recalc_time_report_re.search(output)
        self.assertTrue(found_time_report)
