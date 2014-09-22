# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import time
from textwrap import dedent

import key_codes
from functionaltest import FunctionalTest, snapshot_on_error


class Test_2892_CopyAndPasteFormulaWithErrors(FunctionalTest):

    @snapshot_on_error
    def test_recalc_doesnt_steal_focus_from_usercode(self):
        # Harold logs on and creates a sheet
        self.login_and_create_new_sheet()

        # Harold enters a formula with a sweary error in it
        self.enter_cell_text(1, 1, '=:!&@#&**%!')
        self.wait_for_spinner_to_stop()

        # He then tries to spread the joy by cut & pasting it
        self.copy_range((1, 1), (1, 1))
        self.paste_range((1, 2), (1, 2))

        # He sees the invalid formula in both cells now

        self.wait_for_cell_to_contain_formula(1, 1, '=:!&@#&**%!')
        self.wait_for_cell_to_contain_formula(1, 2, '=:!&@#&**%!')
