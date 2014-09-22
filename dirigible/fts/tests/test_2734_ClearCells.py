# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest
import key_codes
from textwrap import dedent


class Test_2734_ClearCells(FunctionalTest):

    def test_delete_key_clears_selected_cells(self):
        self.assert_key_deletes_cells(key_codes.DELETE)


    def test_backspace_key_clears_selected_cells(self):
        self.assert_key_deletes_cells(key_codes.BACKSPACE)


    def assert_key_deletes_cells(self, key_code):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some data in A1:A3
        self.enter_cell_text(1, 1, 'a1')
        self.enter_cell_text(1, 2, 'a2')
        self.enter_cell_text(1, 3, 'a3')
        self.wait_for_cell_value(1, 3, 'a3')

        # * He clicks on A1 and hits delete
        self.click_on_cell(1, 1)
        self.human_key_press(key_code)

        # * He sees the value in A1 disappear while the others remain
        self.wait_for_cell_value(1, 1, '')
        self.wait_for_cell_value(1, 2, 'a2')
        self.wait_for_cell_value(1, 3, 'a3')

        # * He selects the range a2:a3
        self.select_range_with_shift_click((1, 2), (1, 3))

        # He hits delete
        self.human_key_press(key_code)

        # * He sees that all the cells are now cleared
        self.wait_for_cell_value(1, 1, '')
        self.wait_for_cell_value(1, 2, '')
        self.wait_for_cell_value(1, 3, '')


    def test_delete_key_while_editing_still_does_what_it_should(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters three characters in A1
        self.open_cell_for_editing(1, 1)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * He moves left twice
        self.human_key_press(key_codes.LEFT)
        self.human_key_press(key_codes.LEFT)

        # He hits delete
        self.human_key_press(key_codes.DELETE)

        # the middle character is now missing
        self.wait_for_cell_editor_content('13')


    def test_backspace_key_while_editing_still_does_what_it_should(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters three characters in A1
        self.open_cell_for_editing(1, 1)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * He moves left once
        self.human_key_press(key_codes.LEFT)

        # He hits backspace
        self.human_key_press(key_codes.BACKSPACE)

        # the middle character is now missing
        self.wait_for_cell_editor_content('13')


    def test_can_clear_cell_from_usercode(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some data in A1:A3
        self.enter_cell_text(1, 1, 'a1')
        self.enter_cell_text(1, 2, 'a2')
        self.enter_cell_text(1, 3, 'a3')
        self.wait_for_cell_value(1, 3, 'a3')

        # * He tries to use the clear() function from usercode on a cell
        # and then tries to access some of the supposedly cleared attributes of the cell
        self.prepend_usercode(dedent('''
            worksheet.a1.error = 'harold puts a deliberate pointless error in'

            worksheet.a1.clear()

            worksheet.b1.formula = str(worksheet.a1.value)
            worksheet.b2.formula = str(worksheet.a1.formula)
            worksheet.b3.formula = str(worksheet.a1.formatted_value)
            worksheet.b4.formula = str(worksheet.a1.error)
        '''))

        # * He sees the value in a1 disappear
        self.wait_for_cell_value(1, 1, '')
        self.wait_for_cell_value(1, 2, 'a2')
        self.wait_for_cell_value(1, 3, 'a3')

        # * He sees his little investigations also produce the expected results
        self.wait_for_cell_value(2, 1, '<undefined>')
        self.wait_for_cell_value(2, 2, 'None')
        self.wait_for_cell_value(2, 3, '')
        self.wait_for_cell_value(2, 4, 'None')


    def test_can_clear_cell_range_from_usercode(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some data in A1:A3
        self.enter_cell_text(1, 1, 'a1')
        self.enter_cell_text(1, 2, 'a2')
        self.enter_cell_text(1, 3, 'a3')
        self.wait_for_cell_value(1, 3, 'a3')

        # * He tries to use the clear() function from usercode on a cell range
        self.prepend_usercode(dedent('''
            worksheet.a1.error = 'harold puts a deliberate pointless error in'
            worksheet.a2.error = 'harold puts another deliberate pointless error in'

            worksheet.cell_range("a1:a2").clear()

            worksheet.b1.formula = str(worksheet.a1.value)
            worksheet.b2.formula = str(worksheet.a1.formula)
            worksheet.b3.formula = str(worksheet.a1.formatted_value)
            worksheet.b4.formula = str(worksheet.a1.error)
            worksheet.c1.formula = str(worksheet.a2.value)
            worksheet.c2.formula = str(worksheet.a2.formula)
            worksheet.c3.formula = str(worksheet.a2.formatted_value)
            worksheet.c4.formula = str(worksheet.a2.error)
        '''))
        # * He sees the value in a1 and a2 disappear
        self.wait_for_cell_value(1, 1, '')
        self.wait_for_cell_value(1, 2, '')
        self.wait_for_cell_value(1, 3, 'a3')

        # * He sees his little investigations also produce the expected results
        self.wait_for_cell_value(2, 1, '<undefined>')
        self.wait_for_cell_value(2, 2, 'None')
        self.wait_for_cell_value(2, 3, '')
        self.wait_for_cell_value(2, 4, 'None')

        self.wait_for_cell_value(3, 1, '<undefined>')
        self.wait_for_cell_value(3, 2, 'None')
        self.wait_for_cell_value(3, 3, '')
        self.wait_for_cell_value(3, 4, 'None')
