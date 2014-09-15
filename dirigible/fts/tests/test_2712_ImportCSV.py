# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT

import os


class Test_2712_ImportCSV(FunctionalTest):

    def test_can_import_excel_generated_csv_to_cursor_position(self):
        file_name = 'excel_generated_csv.csv'
        # Harold has a csv file he wants to import into a cloud-based
        # python-infused spreadsheet

        # * Harold logs in to Dirigible and creates a nice shiny new sheet
        self.login_and_create_new_sheet()

        # * After weeks of frustration at being unable to get any data into the app,
        #  it's with great joy that he spots a new button called 'import'
        self.wait_for_element_visibility('id=id_import_button', True)
        self.assertEquals(
            self.selenium.get_attribute('id=id_import_button@alt'),
            "Import a file"
        )
        self.assertEquals(
            self.selenium.get_attribute('id=id_import_button@title'),
            "Import a file"
        )

        #  With preternatural insightfulness, he guesses the button will import
        #  to the current cursor position. Accordingly, he gives himself a
        #  little wriggle room

        self.click_on_cell(2, 2)

        # * He clicks the import CSV button
        self.selenium.click('id=id_import_button')

        # * He is presented with a jquery dialog that contains a file input element
        self.wait_for_element_visibility('id=id_import_form', True)
        self.wait_for_element_visibility('id=id_import_form_file', True)
        self.wait_for_element_visibility('id=id_import_form_upload_csv_button', False)
        self.wait_for_element_visibility('id=id_import_form_upload_xls_values_button', False)
        self.wait_for_element_visibility('id=id_import_form_cancel_button', True)

        #Harold chooses a file, but changes his mind and clicks cancel
        file_name = os.path.join(
            os.path.dirname(__file__), 'test_data', file_name
        )
        self.set_filename_for_upload(file_name, 'id=id_import_form_file')
        self.selenium.click('id=id_import_form_cancel_button')

        # the dialog disappears
        self.wait_for_element_visibility('id=id_import_form', False)

        # harold, keen to get data imported, summons up the strength to try again
        self.selenium.click('id=id_import_button')

        # the dialog reappears
        self.wait_for_element_visibility('id=id_import_form', True)

        # his previous file choice doesn't
        self.assertEquals(
                self.selenium.get_value('id=id_import_form_file'),
                ''
        )

        # * He clicks on the browse button * He is presented with a file-open
        # dialog, and chooses a suitable csv file
        self.set_filename_for_upload(file_name, 'id=id_import_form_file')

        # He spots a radio button, which is defaulted to the 'excel' option
        self.wait_for_element_visibility(
                'css=input[type="radio"][name="csv_encoding"][value="excel"]', True
        )
        self.wait_for_element_visibility(
                'css=input[type="radio"][name="csv_encoding"][value="other"]', True
        )
        self.assertEquals(
            self.selenium.get_value(
                'css=input[type="radio"][name="csv_encoding"][value="excel"]'
            ),
            'on'
        )

        # so he clicks the upload button
        self.wait_for_element_visibility('id=id_import_form_upload_csv_button', True)
        self.selenium.click('id=id_import_form_upload_csv_button')

        # * ...and waits for the page to refresh
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_grid_to_appear()

        # * and is mightily pleased when his data appears at the cursor position.
        self.wait_for_cell_value(2, 2, 'some text')
        self.wait_for_cell_value(3, 2, 'text with quotes "\'""\'"')

        # * In order to check that the cell with a carraige return is imported
        #   ok, he has to check its value via the console, since the \n is
        #   converted to something else for display in the cell
        #self.wait_for_cell_value(4, 2, 'text with a \ncarriage return')
        self.append_usercode('print worksheet.D2.value == "text with a \\ncarriage return"')
        self.wait_for_console_content('True')

        self.wait_for_cell_value(2, 3, 'some european characters:')
        self.wait_for_cell_value(3, 3, u'Herg\xe9')

        self.wait_for_cell_value(2, 4, 'some european money:')
        self.wait_for_cell_value(3, 4, u'pounds: \xa3')
        self.wait_for_cell_value(4, 4, u'euros : \u20ac')
        self.wait_for_cell_value(2, 5, 'numbers')
        self.wait_for_cell_value(2, 6, '1')
        self.wait_for_cell_value(3, 6, '2')
        self.wait_for_cell_value(4, 6, '3000000000')


    def test_can_import_utf8_csv(self):
        # Harold has a kawaii csv file he wants to import into a cloud-based
        # python-infused spreadsheet
        file_name = 'japanese.csv'

        # * He creates a new sheet and clicks the import CSV button
        self.login_and_create_new_sheet()
        self.selenium.click('id=id_import_button')

        # the dialog reappears
        self.wait_for_element_visibility('id=id_import_form', True)

        # * He clicks on the browse button * He is presented with a file-open
        # dialog, and chooses a suitable csv file
        file_name = os.path.join(
            os.path.dirname(__file__), 'test_data', file_name
        )
        self.set_filename_for_upload(file_name, 'id=id_import_form_file')
        # He spots a radio button, which is defaulted to the 'excel' option
        self.wait_for_element_visibility(
                'css=input[type="radio"][name="csv_encoding"][value="excel"]', True
        )
        self.wait_for_element_visibility(
                'css=input[type="radio"][name="csv_encoding"][value="other"]', True
        )
        self.assertEquals(
            self.selenium.get_value(
                'css=input[type="radio"][name="csv_encoding"][value="excel"]'
            ),
            'on'
        )

        # so he changes the radio button option to 'other'
        self.selenium.check(
                'css=input[type="radio"][name="csv_encoding"][value="other"]'
        )

        # and clicks the upload button
        self.wait_for_element_visibility('id=id_import_form_upload_csv_button', True)
        self.selenium.click('id=id_import_form_upload_csv_button')

        # * ...and waits for the page to refresh
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_grid_to_appear()

        # * and is mightily pleased when his kanji appear
        self.wait_for_cell_value(1, 1, u'\u65b0\u4e16\u7d00\u30a8\u30f4\u30a1\u30f3\u30b2\u30ea\u30aa\u30f3')



    def test_bad_files_are_gracefully_handled(self):
        # Harold thinks that if he imports an image file,
        # it will appear in his spreadsheet

        file_name = os.path.join(
            os.path.dirname(__file__), 'test_data', 'import_csv_button.png')

        # * He logs in to Dirigible and creates a nice shiny new sheet
        self.login_and_create_new_sheet()
        sheet_url = self.browser.current_url

        # * He clicks the import toolbar button
        self.selenium.click('id=id_import_button')

        # * He is presented with a jquery dialog that contains a file input element
        self.wait_for_element_visibility('id=id_import_form', True)
        self.wait_for_element_visibility('id=id_import_form_file', True)
        self.wait_for_element_visibility('id=id_import_form_cancel_button', True)

        # * He clicks on the browse button
        # * He is presented with a file-open dialog, and chooses his image file
        self.set_filename_for_upload(file_name, 'id=id_import_form_file')

        # He clicks the upload button
        self.wait_for_element_visibility('id=id_import_form_upload_csv_button', True)
        self.selenium.click('id=id_import_form_upload_csv_button')

        # * ...and waits for the page to refresh
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)

        # * He is presented with an appropriate error page
        self.assertEquals(self.browser.title, "CSV Import Error: Dirigible")
        self.assertEquals(
            self.get_text("id=id_server_error_title"),
            "Could not import CSV file"
        )
        error_text = self.get_text("id=id_server_error_text")
        msg = "Sorry, the file you uploaded was not in a recognised CSV format"
        self.assertTrue(msg  in error_text)

        # * There is a link back to the sheet page, which he follows
        self.click_link('id_sheet_link')

        # And finds himself back on his sheet page.
        self.wait_for_grid_to_appear()
        self.assertEquals(self.browser.current_url, sheet_url)

