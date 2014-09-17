# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import time
from textwrap import dedent

import key_codes
from functionaltest import FunctionalTest, snapshot_on_error


class Test_2892_CellTooltips(FunctionalTest):

    @snapshot_on_error
    def test_formulae_are_shown_in_tooltips(self):
        # Harold logs on and creates a sheet
        self.login_and_create_new_sheet()

        # Harold enters a formula that won't evaluate
        self.enter_cell_text(1, 1, '=A2')
        self.wait_for_spinner_to_stop()

        # He then sees that a tooltip is set on the cell that would show up if
        # he hovered over it

        tooltip = self.selenium.get_attribute(
                self.get_cell_shown_formula_locator(1, 1) + '@title'
        )

        self.assertEquals(tooltip, '=A2')

    @snapshot_on_error
    def test_formatted_values_are_shown_in_tooltips(self):
        # Harold logs on and creates a sheet
        self.login_and_create_new_sheet()

        # Harold enters a piece of text into a cell. Harold knows the basics of
        # spreadsheets...
        self.enter_cell_text(1, 1, 'Maude')
        self.wait_for_spinner_to_stop()

        # He then sees that a tooltip is set on the cell that would show up if
        # he hovered over it

        tooltip = self.selenium.get_attribute(
                self.get_cell_formatted_value_locator(1, 1) + '@title'
        )

        self.assertEquals(tooltip, 'Maude')
