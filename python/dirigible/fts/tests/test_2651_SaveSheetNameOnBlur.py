# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest
from key_codes import ESCAPE

class Test_2651_SaveSheetNameOnBlur(FunctionalTest):

    def test_blur_saves_sheet_name(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He clicks on the sheet name and enters a new one
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'editable sheetname to appear')
        self.selenium.type('id=edit-id_sheet_name', 'clicky namey')

        # * He clicks away from the sheet name
        self.selenium.fire_event('id=edit-id_sheet_name', 'blur')

        # * and notes that his sheet now has the new name
        self.wait_for(
            lambda: self.get_text('id=id_sheet_name') == 'clicky namey',
            lambda: 'sheet name to be updated was "%s"' % (self.get_text('id=id_sheet_name'),)
        )

        # * and the sheet name is not in edit mode
        self.assertFalse(self.selenium.is_element_present('id=edit-id_sheet_name'))


    def test_cancel_instruction_present(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He clicks on the sheet name and enters a new one
        original_name = self.get_text('id=id_sheet_name')
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'editable sheetname to appear')

        # * He enters a new name for the sheet
        self.selenium.type('id=edit-id_sheet_name', "don't really want this")

        # * but then decides that he doesn't want that name, so he hits ESC.
        self.human_key_press(ESCAPE)

        # * The sheet name reverts to the original
        self.assertEquals(self.get_text('id=id_sheet_name'), original_name)
