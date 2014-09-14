# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest

from key_codes import LEFT, LETTER_S


class Test_2726_FormulaBarSelectionDefect(FunctionalTest):

    def test_can_select_text_in_formula_bar(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        long_string = '1234567890' * 10
        self.enter_cell_text(1, 1, long_string)
        self.wait_for_cell_value(1, 1, long_string)
        self.click_on_cell(1, 1)

        self.selenium.click('id=id_formula_bar')
        self.human_key_press(LEFT)
        self.human_key_press(LEFT)
        self.human_key_press(LEFT)
        self.human_key_press(LEFT)
        self.human_key_press(LEFT)
        self.human_key_press(LEFT)

        self.selenium.click('id=id_formula_bar')

        self.human_key_press(LETTER_S)
        self.human_key_press(LETTER_S)
        self.assertTrue(
            self.selenium.get_value(
                self.get_formula_bar_locator()).endswith(
                '1234ss567890'
            )
        )
