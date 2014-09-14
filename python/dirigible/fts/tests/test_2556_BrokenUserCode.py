# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, snapshot_on_error


class test_2556_BrokenUsercode(FunctionalTest):

    @snapshot_on_error
    def test_newly_entered_formulae_appear_grey_then_results_in_black(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # make recalc slow, so that we can be sure to see cells
        # passing through their intermediate 'sent to server
        # but not yet evaluated' state
        # Set 2,2 to ready to be sure this usercode change is made before
        # proceeding.
        self.prepend_usercode('import time\ntime.sleep(20.0)\nworksheet[2,2].formula="ready"')
        self.wait_for_cell_value(2, 2, 'ready', timeout_seconds=22)

        # check intermediate state then final state after entering a formula
        self.enter_cell_text(1, 2, '=123')
        self.wait_for_cell_shown_formula(1, 2, '=123', timeout_seconds=19)
        self.wait_for_cell_value(1, 2, '123', timeout_seconds=30)


    def test_broken_usercode_returns_as_much_as_it_can(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        original_usercode = self.get_usercode()

        # * He enters a constant and a formula in the sheet
        self.enter_cell_text(1, 1, 'abc')
        self.enter_cell_text(1, 2, '=123')
        self.wait_for_cell_value(1, 2, '123')

        # * He adds a usercode error before the constants get calculated
        self.prepend_usercode('x=1/0')

        self.enter_cell_text(2, 1, 'def')
        self.enter_cell_text(2, 2, '=456')
        self.wait_for_cell_shown_formula(2, 2, '=456')

        self.assert_cell_shown_formula(1, 1, 'abc')
        self.assert_cell_shown_formula(1, 2, '=123')
        self.assert_cell_shown_formula(2, 1, 'def')
        self.assert_cell_shown_formula(2, 2, '=456')

        # * He adds a usercode error between constants and formulae

        def insert(text):
            insertion_point = original_usercode.find('evaluate_formulae(worksheet)')
            return "%s\n%s\n%s" % (
                original_usercode[:insertion_point],
                text,
                original_usercode[insertion_point:],
            )

        usercode = insert('x=1/0\n')
        self.enter_usercode(usercode)

        self.enter_cell_text(3, 1, 'ghi')
        self.enter_cell_text(3, 2, '=789')
        self.wait_for_cell_shown_formula(3, 2, '=789')

        self.assertEquals(self.get_cell_text(1, 1), 'abc')
        self.assert_cell_shown_formula(1, 2, '=123')
        self.assertEquals(self.get_cell_text(2, 1), 'def')
        self.assertEquals(self.get_cell_text(2, 2), '=456')
        self.assertEquals(self.get_cell_text(3, 1), 'ghi')
        self.assertEquals(self.get_cell_text(3, 2), '=789')

        # * He adds a usercode error after formulae
        self.enter_usercode(original_usercode)
        self.append_usercode('x=1/0')

        self.enter_cell_text(4, 1, 'jkl')
        self.enter_cell_text(4, 2, '=100')
        self.wait_for_cell_value(4, 2, '100')

        self.assertEquals(self.get_cell_text(1, 1), 'abc')
        self.assertEquals(self.get_cell_text(1, 2), '123')
        self.assertEquals(self.get_cell_text(2, 1), 'def')
        self.assertEquals(self.get_cell_text(2, 2), '456')
        self.assertEquals(self.get_cell_text(3, 1), 'ghi')
        self.assertEquals(self.get_cell_text(3, 2), '789')
        self.assertEquals(self.get_cell_text(4, 1), 'jkl')
        self.assertEquals(self.get_cell_text(4, 2), '100')

        # \o/ hooray!

