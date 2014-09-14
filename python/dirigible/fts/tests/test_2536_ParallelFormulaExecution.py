# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent
import re

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest, snapshot_on_error

took_regex = re.compile('Took ([^s]+)s')

class Test_2536_ParallelFormulaExecution(FunctionalTest):

    def get_last_recalc_time(self):
        match = took_regex.match(self.get_console_content())
        return float(match.group(1))

    @snapshot_on_error
    def test_formulae_executed_in_parallel(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * Harold enters some usercode to provide formulae that take time to calculate
        self.prepend_usercode(dedent('''
        import time
        def slow_product(val1, val2):
            time.sleep(1)
            return val1 * val2
        '''))

        # * he enters a tree of dependent cell formula which use slow_product
        self.enter_cell_text(1, 3, '=slow_product(1, 2)')
        self.enter_cell_text(2, 3, '=slow_product(3, 4)')
        self.enter_cell_text(3, 3, '=slow_product(5, 6)')
        self.enter_cell_text(4, 3, '=slow_product(7, 8)')

        self.enter_cell_text(1, 2, '=slow_product(A3, B3)')
        self.enter_cell_text(2, 2, '=slow_product(C3, D3)')

        self.enter_cell_text(1, 1, '=slow_product(A2, B2)')

        # * and waits for the sheet to calculate
        self.wait_for_cell_value(1, 1, '40320', timeout_seconds=10)

        # * He notes the the recalculation was much faster than he would
        #   expect if the formulae had been run in series
        # Note: There are 7 formulae in 3 dependency 'layers' so we expect
        # the recalc to take about 3sec.
        self.assertTrue(
            self.get_last_recalc_time() < 3.2,
            'calculation took too long - %ss. Parallel broken?' % (self.get_last_recalc_time(),)
        )

    @snapshot_on_error
    def test_run_worksheet_executed_in_parallel(self):
        # * Harold logs in and creates a blank worker sheet
        self.login_and_create_new_sheet()
        worker_sheet_url = self.browser.current_url

        # * He then goes to create a master sheet that makes several calls on the worker
        self.create_new_sheet()
        master_sheet_url = self.browser.current_url

        # * he enters formulae that use the worksheet in a number of run_worksheet calls
        run_worksheet_formula = '=run_worksheet("%s")[1, 1].value' % (worker_sheet_url,)
        for row in range(1, 5):
            self.enter_cell_text(1, row, run_worksheet_formula)


        # * Harold goes back to the worker and enters some usercode to make a recalc slow
        self.go_to_url(worker_sheet_url)
        self.wait_for_grid_to_appear()

        self.prepend_usercode(dedent('''
        import time
        start = time.time()
        x = 1
        while time.time() - start < 10:
            time.sleep(0.5)
            x += 1
        worksheet[1, 1].value = x
        '''))
        self.wait_for_spinner_to_stop(timeout_seconds=15)

        # * He now goes back to the master sheet,
        self.go_to_url(master_sheet_url)
        self.wait_for_grid_to_appear()

        # * He notes the the recalculation was much faster than he would
        #   expect if the run_worksheets had been run in series
        self.wait_for_spinner_to_stop(timeout_seconds=15)
        self.assertTrue(self.get_last_recalc_time() < 19, 'calculation took too long. Parallel recalc broken?')

