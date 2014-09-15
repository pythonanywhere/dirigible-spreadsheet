# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest, humanesque_delay
import key_codes


class Test_2812_CutCopyPasteInEditMode(FunctionalTest):

    def test_delete_key_while_editing_still_does_what_it_should(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters three characters in A1
        self.open_cell_for_editing(1, 1)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * He hits ctrl-A
	with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_A)

        # He hits control-X
	with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_X)

        # the text is gone
        self.wait_for_cell_editor_content('')

        # He hits control-V
	with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_V)

	# His cut text returns
        self.wait_for_cell_editor_content('123')

        # * He selects everything again
	with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_A)

        # He hits control-C
	with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_C)

        # Nothing happens to his carefully-crafted text
        self.wait_for_cell_editor_content('123')

        # He hits control-V twice
	with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_V)
            self.human_key_press(key_codes.LETTER_V)

	# and is presented with his final masterpiece
        self.wait_for_cell_editor_content('123123')
