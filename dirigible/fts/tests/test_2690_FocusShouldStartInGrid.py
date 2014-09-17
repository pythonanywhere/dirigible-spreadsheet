# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest
import key_codes


class test_2690_FocusShouldStartInGrid(FunctionalTest):

    def test_focus(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * The focus is initially in A1
        # (not in text editor where it is annoying since clicking on
        # grid then causes unwanted recalcs. Especially annoying after
        # loading a large sheet)

        # Hence, Harold starts typing...
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * The formula he typed appears in cell A1's edit box
        self.wait_for_cell_to_enter_edit_mode(1, 1)
        self.wait_for_cell_editor_content('123')

