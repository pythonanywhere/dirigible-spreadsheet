# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest
import key_codes


class Test_2635_SheetNameSelectedOnEdit(FunctionalTest):

    def test_click_on_sheet_name(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He clicks on the sheet name and enters a new one
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.is_element_present('id=edit-id_sheet_name'),
            lambda: 'editable sheetname to appear')
        self.human_key_press(key_codes.LETTER_A)
        self.human_key_press(key_codes.LETTER_B)
        self.wait_for(
            lambda: self.selenium.get_value('id=edit-id_sheet_name') == 'ab',
            lambda: 'sheetname to change')

