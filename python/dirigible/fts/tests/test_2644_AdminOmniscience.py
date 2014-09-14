# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2644_AdminOmniscience(FunctionalTest):
    user_count = 2

    def test_staff_can_see_everything(self):
        # Harold logs in to Dirigible and creates a new sheet and puts some
        # super-sekrit data in it.
        self.login_and_create_new_sheet()
        self.enter_cell_text(1, 1, "My banking password")
        harolds_sheet_url = self.selenium.get_location()
        self.wait_for_cell_value(1, 1, 'My banking password')

        # He logs out, confident that it's safe from prying eyes.
        self.logout()

        # A member of Dirigible staff logs in, tries to view his sheet and
        # sees it.
        self.login(username='admin', password='admin password?')
        self.go_to_url(harolds_sheet_url)
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(1, 1, "My banking password")


    def test_non_staff_cannot_view_or_edit_other_users_sheets_or_json(self):
        harriet = self.get_my_usernames()[1]
        harold = self.get_my_username()

        # Harriet creates a sheet containing her private data.
        self.login_and_create_new_sheet(username=harriet)
        harriets_sheet_url = self.selenium.get_location()
        self.logout()

        # Before logging in, Harold tries to access Harriet's sheet using the
        # correct direct URL, with *her* username and the correct sheet ID.
        # He gets redirected to the login page
        self.assert_sends_to_login_page(harriets_sheet_url)
        self.assert_sends_to_login_page('%scalculate/' % (harriets_sheet_url,))
        self.assert_sends_to_login_page(
            '%sset_cell_formula/' % (harriets_sheet_url,))
        self.assert_sends_to_login_page(
            '%sget_json_grid_data_for_ui/' % (harriets_sheet_url,))
        self.assert_sends_to_login_page(
            '%sget_json_meta_data_for_ui/' % (harriets_sheet_url,))

        # After logging in, Harold tries to access the same sheet
        # using the correct direct URL, with *her* username and the
        # correct sheet ID.
        # He gets a 403 (Access denied) error
        self.login(username=harold)
        self.assert_HTTP_error(harriets_sheet_url, 403)
        self.assert_HTTP_error('%scalculate/' % (harriets_sheet_url,), 403)
        self.assert_HTTP_error(
            '%sget_json_grid_data_for_ui/' % (harriets_sheet_url,), 403)
        self.assert_HTTP_error(
            '%sget_json_meta_data_for_ui/' % (harriets_sheet_url,), 403)
        self.assert_HTTP_error(
            '%sset_cell_formula/' % (harriets_sheet_url,), 403)

