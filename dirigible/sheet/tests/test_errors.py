# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
from textwrap import dedent

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import sentinel, Mock

from sheet.cell import undefined
from sheet.errors import CycleError, report_cell_error
from sheet.worksheet import Worksheet


class TestCycleError(unittest.TestCase):

    def test_cycle_error_str_reports_path(self):
        ce1 = CycleError([(1, 2), (4, 5), (1, 2)])
        self.assertEquals(str(ce1), 'A2 -> D5 -> A2')


    def test_cycle_error_repr_reports_path(self):
        ce1 = CycleError([(1, 2), (4, 5), (1, 2)])
        self.assertEquals(repr(ce1), 'CycleError(A2 -> D5 -> A2)')


    def test_cycle_errors_compare_unequal_to_random_crap(self):
        ce1 = CycleError([(1, 2), (4, 5), (1, 2)])
        self.assertFalse(ce1 == object())
        self.assertTrue(ce1 != object())


    def test_cycle_errors_compare_equal_from_identical_path(self):
        ce1 = CycleError([(1, 2), (4, 5), (1, 2)])
        ce2 = CycleError([(1, 2), (4, 5), (1, 2)])
        self.assertTrue(ce1 == ce2)
        self.assertFalse(ce1 != ce2)


    def test_cycle_errors_compare_unequal_from_different_paths(self):
        ce1 = CycleError([(1, 2), (4, 5), (1, 2)])
        ce2 = CycleError([(1, 2), (4, 6), (1, 2)])
        self.assertFalse(ce1 == ce2)
        self.assertTrue(ce1 != ce2)


class TestReportCellError(unittest.TestCase):

    def test_report_cell_error(self):
        worksheet = Worksheet()
        worksheet.add_console_text = Mock()
        worksheet[1, 2].formula = '=A1'

        report_cell_error(worksheet, (1, 2), ZeroDivisionError('hello'))

        self.assertEqual(
            worksheet[(1, 2)].error,
            'ZeroDivisionError: hello'
            )
        self.assertEqual(
            worksheet[(1, 2)].value,
            undefined
            )
        expected_error_text = dedent('''
            ZeroDivisionError: hello
                Formula '=A1' in A2
            ''')[1:]
        self.assertEqual(
            worksheet.add_console_text.call_args_list,
            [((expected_error_text,), {})],
            )


