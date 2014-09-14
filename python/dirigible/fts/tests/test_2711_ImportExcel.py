# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT, Url

import os

SHEET1 = 'first sheet'
SHEET2 = '2nd'
EMPTY_SHEET = 'empty sheet'


class Test_2711_Import_Excel(FunctionalTest):

    def test_can_import_excel_values_only_from_sheet_page(self):
        # Harold has an excel file he wants to import into a cloud-based
        # python-infused spreadsheet

        # * Harold logs in to Dirigible
        self.login_and_create_new_sheet()

        # * He spots the 'import' button
        self.wait_for_element_visibility('id=id_import_button', True)
        self.assertEquals(
                self.selenium.get_attribute('id=id_import_button@alt'),
                "Import a file"
        )
        self.assertEquals(
                self.selenium.get_attribute('id=id_import_button@title'),
                "Import a file"
        )

        # * He clicks the import button
        self.selenium.click('id=id_import_button')

        # * He is presented with a jquery dialog that contains a file input element
        self.wait_for_element_visibility('id=id_import_form', True)
        self.wait_for_element_visibility('id=id_import_form_file', True)
        self.wait_for_element_visibility('id=id_import_form_upload_csv_button', False)
        self.wait_for_element_visibility('id=id_import_form_upload_xls_values_button', False)
        self.wait_for_element_visibility('id=id_import_form_cancel_button', True)
        
        # * Harold panics at seeing something new, and clicks the cancel button
        self.selenium.click('id=id_import_form_cancel_button')

        # the dialog disappears
        self.wait_for_element_visibility('id=id_import_form', False)

        # Harold, keen to get data imported, summons up the strength to try again
        self.selenium.click('id=id_import_button')

        # the dialog reappears.
        self.wait_for_element_visibility('id=id_import_form', True)

        # * He clicks on the file browse button. He is presented with a
        #   file-open dialog, and chooses a suitable excel file
        file_name = os.path.join(
                os.path.dirname(__file__),
                'test_data', 'T2711-import-excel.xls'
        )
        self.set_filename_for_upload(file_name, 'id=id_import_form_file')

        # the upload excel buttons appear
        self.wait_for_element_visibility(
                'id=id_import_form_upload_xls_values_button', True)

        # so he clicks one
        self.selenium.click('id=id_import_form_upload_xls_values_button')

        # * ...and gets redirected to his dashboard
        self.selenium.wait_for_page_to_load(10000)
        self.selenium.open(Url.ROOT)
        self.selenium.wait_for_page_to_load(10000)

        # He notices 3 new sheets added to his dashboard
        page_text = self.selenium.get_html_source()
        self.assertTrue('T2711-import-excel - first sheet' in page_text)
        self.assertTrue('T2711-import-excel - 2nd' in page_text)
        self.assertTrue('T2711-import-excel - error sheet' in page_text)
        self.assertTrue('T2711-import-excel - empty sheet' not in page_text)

        # He visits the first one to check that the values there are
        # the same as the ones in the Excel file
        self.selenium.click('link=T2711-import-excel - first sheet')
        self.selenium.wait_for_page_to_load(10000)
        self.wait_for_grid_to_appear()

        self.wait_for_cell_value(1, 1, "Spell")
        self.wait_for_cell_value(2, 1, "Arc")
        self.wait_for_cell_value(3, 1, "Bar")
        self.wait_for_cell_value(1, 2, "attack")
        self.wait_for_cell_value(14, 8, "E")

        # he goes back to the dashboard
        self.selenium.open(Url.ROOT)
        self.selenium.wait_for_page_to_load(10000)

        # He visits the second sheet to check that the values there are
        # the same as the ones in the Excel file
        self.selenium.click('link=T2711-import-excel - 2nd')
        self.selenium.wait_for_page_to_load(10000)
        self.wait_for_grid_to_appear()

        self.wait_for_cell_value(1, 1, "sauce")
        self.wait_for_cell_value(3, 4, "27.5")

        # he goes back to the dashboard
        self.selenium.open(Url.ROOT)
        self.selenium.wait_for_page_to_load(10000)

        # He visits the third sheet to check that the values there are
        # the same as the ones in the Excel file
        self.selenium.click('link=T2711-import-excel - error sheet')
        self.selenium.wait_for_page_to_load(10000)
        self.wait_for_grid_to_appear()

        self.wait_for_cell_value(1, 1, "1979-10-08 00:00:00")
        self.click_on_cell(2, 1)
        self.wait_for_formula_bar_contents("=#NUM!")
        self.click_on_cell(3, 1)
        self.wait_for_formula_bar_contents("=#DIV/0!")


    def test_bad_files_are_gracefully_handled(self):
        # Harold thinks that if he imports an image file,
        # it will appear in his spreadsheet

        # * He logs in to Dirigible and creates a nice shiny new sheet
        self.login_and_create_new_sheet()
        sheet_url = self.browser.current_url

        # * He clicks the import button
        self.selenium.click('id=id_import_button')

        # * He is presented with a jquery dialog that contains a file input
        # element
        self.wait_for_element_visibility('id=id_import_form', True)

        # * He clicks on the browse button
        # * He is presented with a file-open dialog, and chooses his image file
        file_name = os.path.join(
                os.path.dirname(__file__),
                'test_data', 'T2711-badly-named-png.xls'
        )
        self.set_filename_for_upload(file_name, 'id=id_import_form_file')

        # He clicks the upload excel values only button
        self.selenium.click('id=id_import_form_upload_xls_values_button')

        # * ...and waits for the page to refresh
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)

        # * He is presented with an appropriate error page
        self.assertEquals(
                self.selenium.get_title(), "Excel Import Error: Dirigible")
        self.assertEquals(
                self.get_text("id=id_server_error_title"),
                "Could not import Excel file"
        )
        error_text = self.get_text("id=id_server_error_text")
        msg = "Sorry, the file you uploaded was not imported"
        self.assertTrue(msg in error_text)

        # * There is a link back to his account page, which he follows
        self.click_link('id_account_link')

        # And finds himself back on his sheet page.
        self.assertEquals(self.browser.current_url, Url.ROOT)

