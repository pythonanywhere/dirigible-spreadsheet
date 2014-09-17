# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

from functionaltest import FunctionalTest
import key_codes

class Test_2654_CtrlSSavesUsercode(FunctionalTest):

    def test_ctrl_s_saves_usercode(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some usercode
        self.selenium.get_eval('window.editor.focus()')
        self.enter_usercode('worksheet[1, 1].value = 5', commit_change=False)

        # * and presses Ctrl-S
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_S)

        # * His usercode gets saved and a recalculation starts
        #self.wait_for_cell_value(1, 1, '5')

        # He types a few more characters, which should appear in the usercode
        # box, because the save-as dialog didn't appear to capture them
        self.human_key_press(key_codes.LETTER_A)
        self.human_key_press(key_codes.LETTER_A)
        self.human_key_press(key_codes.LETTER_A)

        ## NB enter_usercode leaves the cursor at the end of the editor.
        self.wait_for_usercode_editor_content(
            'worksheet[1, 1].value = 5aaa'
        )


