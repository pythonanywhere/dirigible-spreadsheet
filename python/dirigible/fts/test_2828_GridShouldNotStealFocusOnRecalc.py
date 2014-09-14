# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

import key_codes
from functionaltest import FunctionalTest, snapshot_on_error


class Test_2828_GridShouldNotStealFocusOnRecalc(FunctionalTest):

    @snapshot_on_error
    def test_recalc_doesnt_steal_focus_from_usercode(self):
        # Harold logs on and creates a sheet
        self.login_and_create_new_sheet()

        # Harold enters some usercode that takes a while to recalc
        # setting a value in the grid
        self.enter_usercode(dedent('''
            import time
            time.sleep(5)
        '''))

        # while the recalc is running he types something in the editor
        #self.selenium.focus('id=id_usercode')
        self.selenium.get_eval('window.editor.focus()')
        self.human_key_press(key_codes.LETTER_A)

        # When the recalc comes back, he types some more text, and notes with
        # satifaction that the grid has not stolen the focus
        self.wait_for_spinner_to_stop()
        self.human_key_press(key_codes.LETTER_A)

        self.wait_for(
            lambda : 'aa' in self.get_usercode(),
            lambda : "Usercode editor didn't contain aa::\n%s" % (
                self.get_usercode(),
            ),
        )

