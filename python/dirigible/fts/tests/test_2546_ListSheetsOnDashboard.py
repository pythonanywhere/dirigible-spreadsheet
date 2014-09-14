# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, SERVER_IP, snapshot_on_error

import key_codes


class Test_2546_ListSheetsOnDashboard(FunctionalTest):

    def rename_current_sheet(self, name):
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'edit sheetname textbox to appear')
        self.selenium.type('id=edit-id_sheet_name', name)
        self.human_key_press(key_codes.ENTER)
        self.wait_for_element_presence('id=saving-id_sheet_name', False)


    def assert_sheet_is_listed(self, sheet_id, sheet_name=None):
        if sheet_name is None:
            sheet_name = 'Sheet %s' % (sheet_id,)
        expected_url = '/user/%s/sheet/%s/' % (self.get_my_username(), sheet_id)
        link_text = self.get_text(
            'css=a[href="%s"]' % (expected_url,))
            # "xpath=//a[contains(@href, '%s')]" % (expected_url,))
        self.assertEquals(link_text, sheet_name)


    @snapshot_on_error
    def test_list_exists(self):
        # * Harold logs in to Dirigible.
        self.login()

        # * He notes that he is being told that he has no sheets.
        self.assertTrue(
            self.selenium.is_element_present('id=id_no_sheets_message'),
            "Could not find 'no sheets' message"
        )

        # * He decides that he wants one, so he clicks on a button to create it.
        sheet1_id = self.create_new_sheet()

        # * He clicks 'my account' and goes back to dashboard page
        # * His new sheet is listed there, with a link to it
        self.click_link('id_account_link')
        self.assert_sheet_is_listed(sheet1_id)

        # He notes that the "no sheets" message is absent.
        self.assertFalse(
            self.selenium.is_element_present('id=id_no_sheets_message'),
            "Found 'no sheets' message when it wasn't expected"
        )


        # * He clicks new sheet again
        sheet2_id = self.create_new_sheet()
        # * He renames the second sheet
        self.rename_current_sheet('Snarf')

        # * He clicks 'my account' and goes back to dashboard page
        self.click_link('id_account_link')
        # * Both sheets are listed there
        self.assert_sheet_is_listed(sheet1_id)
        self.assert_sheet_is_listed(sheet2_id, 'Snarf')

