# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2839_CutCopyPasteButtons(FunctionalTest):

    def test_buttons_exist_and_are_clickable(self):
        # * Harold logs in to Dirigible and creates a nice shiny new sheet
        self.login_and_create_new_sheet()

        # * He sees that toolbar buttons exist for cut, copy, paste
        self.wait_for_element_visibility('id=id_cut_button', True)
        self.wait_for_element_visibility('id=id_copy_button', True)
        self.wait_for_element_visibility('id=id_paste_button', True)

        # * He enters a simple cell value
        self.enter_cell_text(1, 1, "Sausage")

        # * He cuts it using the toolbar button, and it dissapears
        self.click_on_cell(1, 1)
        self.selenium.click('id=id_cut_button')
        self.wait_for_cell_value(1, 1, '')

        # * He pastes it elsewhere, he confirms it appears there
        self.click_on_cell(2, 1)
        self.selenium.click('id=id_paste_button')
        self.wait_for_cell_value(2, 1, 'Sausage')

        # * He copies it and pastes elsewhere
        self.click_on_cell(2, 1)
        self.selenium.click('id=id_copy_button')
        self.click_on_cell(3, 1)
        self.selenium.click('id=id_paste_button')
        # * He makes sure the data is visible in both locations
        self.wait_for_cell_value(3, 1, 'Sausage')
        self.wait_for_cell_value(2, 1, 'Sausage')
