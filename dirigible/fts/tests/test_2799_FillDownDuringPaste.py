# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest
import key_codes


class Test_2799_fill_down_during_paste(FunctionalTest):

    def wait_for_cell_to_contain_formula(self, column, row, formula):
        self.open_cell_for_editing(column, row)
        self.wait_for_cell_editor_content(formula)
        self.human_key_press(key_codes.ENTER)


    def test_fill_down_formula_with_copy_and_paste(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold populates a table full of data
        self.enter_cell_text(1, 1, '1')
        self.enter_cell_text(2, 1, '1')
        self.enter_cell_text(1, 2, '2')
        self.enter_cell_text(2, 2, '2')
        self.enter_cell_text(1, 3, '3')
        self.enter_cell_text(2, 3, '3')

        # * He writes a function to sum the values in a row
        self.enter_cell_text(3, 1, '=A1+B1')

        # * He uses copy & paste to 'fill down' his formula
        self.copy_range((3, 1), (3, 1))
        self.paste_range((3, 2), (3, 3))

        self.wait_for_cell_to_contain_formula(3, 2, '=A2+B2')
        self.wait_for_cell_to_contain_formula(3, 3, '=A3+B3')


    def test_fill_down_2x2_clipboard_into_3x5_selection(self):
        # * Harold logs in to dirigible, his favourite cloud computing tool
        self.login_and_create_new_sheet()

        # * Harold populates a table full of data
        self.enter_cell_text(1, 1, '=C1')
        self.enter_cell_text(2, 1, '=D1')
        self.enter_cell_text(1, 2, '=C2')
        self.enter_cell_text(2, 2, '=D2')

        # * He uses copy & paste to 'fill down' his formula
        self.copy_range((1, 1), (2, 2))
        self.paste_range((3, 3), (5, 7))

        self.wait_for_cell_to_contain_formula(3, 3, '=E3')
        self.wait_for_cell_to_contain_formula(4, 3, '=F3')
        self.wait_for_cell_to_contain_formula(5, 3, '=G3')

        self.wait_for_cell_to_contain_formula(3, 4, '=E4')
        self.wait_for_cell_to_contain_formula(4, 4, '=F4')
        self.wait_for_cell_to_contain_formula(5, 4, '=G4')
        
        self.wait_for_cell_to_contain_formula(3, 5, '=E5')
        self.wait_for_cell_to_contain_formula(4, 5, '=F5')
        self.wait_for_cell_to_contain_formula(5, 5, '=G5')
        
        self.wait_for_cell_to_contain_formula(3, 6, '=E6')
        self.wait_for_cell_to_contain_formula(4, 6, '=F6')
        self.wait_for_cell_to_contain_formula(5, 6, '=G6')
        
        self.wait_for_cell_to_contain_formula(3, 7, '=E7')
        self.wait_for_cell_to_contain_formula(4, 7, '=F7')
        self.wait_for_cell_to_contain_formula(5, 7, '=G7')

        self.wait_for_cell_to_contain_formula(3, 8, '')
        self.wait_for_cell_to_contain_formula(4, 8, '')
        self.wait_for_cell_to_contain_formula(5, 8, '')

        self.wait_for_cell_to_contain_formula(6, 3, '')
        self.wait_for_cell_to_contain_formula(6, 4, '')
        self.wait_for_cell_to_contain_formula(6, 5, '')
        self.wait_for_cell_to_contain_formula(6, 6, '')
        self.wait_for_cell_to_contain_formula(6, 7, '')

