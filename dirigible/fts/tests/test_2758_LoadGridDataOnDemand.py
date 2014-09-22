# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

from functionaltest import FunctionalTest
import key_codes

from textwrap import dedent


class Test_2758_LoadGridDataOnDemand(FunctionalTest):

    def test_grid_data_loaded_on_demand_for_rows(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * Using usercode, he puts a blob of data far down and to
        #   the right in the sheet.
        self.append_usercode(dedent("""
            for col in range(1, 53):
                for row in range(600, 1001):
                    worksheet[col, row].value = "(%s, %s)" % (col, row)
        """))

        # * He waits for the recalc to complete.
        self.wait_for_spinner_to_stop()
        # He makes sure the grid has focus for the subsequent keypress
        self.click_on_cell(1, 1)

        # * then types Ctrl-End
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.END)

        # * The grid scrolls down and to the right, but the cells are initially
        #   empty
        self.wait_for_cell_to_be_visible(52, 1000)
        self.wait_for_cell_value(52, 1000, '')

        # * A "Buffering" window appears, relatively briefly
        self.wait_for_element_visibility("id=id_buffering_message", True)

        # * When the "buffering" window disappears, the data is there.
        self.wait_for_element_visibility("id=id_buffering_message", False)
        self.wait_for_cell_value(52, 1000, '(52, 1000)')

