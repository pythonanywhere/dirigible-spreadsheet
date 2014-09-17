# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import time
from textwrap import dedent

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2549_InterruptedRecalculations(FunctionalTest):

    @snapshot_on_error
    def test_interrupted_recalc_coming_back_handled_correctly(self):
        # Harold logs on and creates a sheet
        self.login_and_create_new_sheet()

        # Harold enters a long-running recalc that finishes by
        # setting a value in the grid
        self.enter_usercode(dedent('''
            import time
            time.sleep(20)
            worksheet[1, 5].value = 1
        '''))

        # While it is running, he realises that there is a shorter
        # algorithm, so he tries that instead.
        time.sleep(1)
        self.enter_usercode(dedent('''
            worksheet[1, 5].value = 2
        '''))

        # Even though the initial longer-running recalc finishes
        # after the second one, the result he sees is from the
        # second one; he concludes that the results of the first
        # one must have been thrown away.
        self.wait_for_cell_value(1, 5, '2')

        # To confirm this to himself, he waits until the first
        # recalc has absolutely definitely finished, and confirms
        # that its results never appear in the grid.
        time.sleep(30)
        self.wait_for_cell_value(1, 5, '2')

        # He then refreshes his web page to make sure that the
        # correct version is current in the database.
        self.refresh_sheet_page()
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(1, 5, '2')
