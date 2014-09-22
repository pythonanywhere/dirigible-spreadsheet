# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

from functionaltest import FunctionalTest
import key_codes


class Test_2735_CtrlKeysArePassedToBrowser(FunctionalTest):

    def test_ctrl_t(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He clicks the grid then types ctrl-t
        self.click_on_cell(1, 1)
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_T)

        # * A new tab has been opened.  NB no way to test this
        #   was found after quite a while investigating.
        # * Harold switches back
        self.selenium.select_window('null')

        # * The current cell is not being edited.
        self.assert_cell_is_current_but_not_editing(1, 1)
        # * The current cell does not contain a 't'
        self.assertEquals('', self.get_cell_text(1, 1))

