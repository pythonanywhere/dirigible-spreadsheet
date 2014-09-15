# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from selenium.webdriver.common.keys import Keys
from urlparse import urlparse

from functionaltest import FunctionalTest, snapshot_on_error, Url


class Test_2528_CreateEditSheet(FunctionalTest):
    user_count = 2

    def assert_editing_cell(self, column, row):
        self.assertTrue(self.is_element_present(
            self.get_cell_editor_locator(column, row)
        ))


    @snapshot_on_error
    def test_create_edit_sheet(self):
        # * Harold logs in to Dirigible.
        self.login()

        # * On his dashboard, he notes an option to create a new spreadsheet.  He chooses it.
        self.assertEquals(self.get_text('id=id_create_new_sheet'), "Create new sheet...")
        self.click_link('id_create_new_sheet')

        # * He is taken to a web page which has a URL like /user/XXXX/sheet/<num>
        #        where XXXX is his user name
        _, __, path, ___, ____, _____ = urlparse(self.browser.current_url)
        self.assertRegexpMatches(path, '/user/%s/sheet/[0-9]+/' % (self.get_my_username(),))

        # * The page has a grid.
        print('check grid')
        self.assertTrue(self.is_element_present('id=id_grid'))

        # * He sees that the grid is a usable size (at least 100x100)
        print('check grid 2')
        self.wait_for_grid_to_appear()
        print('check width')
        self.assertTrue(self.get_element('id=id_grid').size['width'] >= 100)
        self.assertTrue(self.get_element('id=id_grid').size['height'] >= 100)

        # * Now that the grid is loaded (and so the sheet's name is too), he notices
        #   that the title is something like: XXXX's sheet_name: Dirigible
        sheet_name = self.get_text('id=id_sheet_name')
        self.assertEquals(
            self.browser.title,
            "%s's %s: Dirigible" % (self.get_my_username(), sheet_name)
        )


        # * He sees that the grid is reasonably layed out, and it has a sensible
        #   number of rows and columns (at least 10x10), the columns having
        #   headers A, B, C etc and the rows 1, 2, 3,...
        column_list_css = 'div.slick-header-column span.slick-column-name'

        def get_columns():
            return self.browser.find_elements_by_css_selector(column_list_css)

        ## Check for 10 cols plus one header col
        print('check num cols')
        self.wait_for(
            lambda: len(get_columns()) >= 11,
            lambda: 'column count to become >= 11, was {}'.format(len(get_columns())),
        )

        print('col positions')
        col_header_vertical_positions = []
        for letter in 'ABCDEFG':
            column = self.get_element("css=div.slick-header-column[title={}]".format(letter))
            col_header_vertical_positions.append(column.location['y'])
        self.assertEquals(len(set(col_header_vertical_positions)), 1)

        print('col positions horiz')
        col_header_horizontal_positions = []
        for letter in 'ABCDEFG':
            column = self.get_element("css=div.slick-header-column[title={}]".format(letter))
            col_header_horizontal_positions.append(column.location['x'])
        self.assertEquals(
            col_header_horizontal_positions, sorted(col_header_horizontal_positions)
        )

        print('col headers')
        column_headers = [c.text for c in get_columns()]
        print(column_headers)
        self.assertEquals(''.join(column_headers[:8]), "ABCDEFG")  # starts with one blank

        ## Check for 10 rows plus one header row
        print('rows')
        row_list_css = 'div.slick-row'
        rows = self.browser.find_elements_by_css_selector(row_list_css)
        ## SlickGrid handles the header row for us, so we don't have to check for it
        self.assertGreater(len(rows), 9)
        row_header_vertical_positions = []
        for row in rows:
            row_header_vertical_positions.append(row.location['y'])

        self.assertEquals(row_header_vertical_positions, sorted(row_header_vertical_positions))

        row_header_horizontal_positions = set()
        for row in rows:
            row_header_horizontal_positions.add(row.location['x'])
        self.assertEquals(len(row_header_horizontal_positions), 1)

        row_headers = ''.join(r.text for r in rows)
        self.assertEquals(row_headers[:9], "123456789")

        # * He enters "1" in A1.
        self.enter_cell_text(1, 1, '1')

        # * When he moves away from the cell, "1" is there
        self.click_on_cell(2, 2)
        self.wait_for_cell_value(1, 1, '1')

        # * He enters "2" in A2.  Similarly, this persists when he moves away.
        self.enter_cell_text(1, 2, '2')
        self.click_on_cell(2, 3)
        self.wait_for_cell_value(1, 2, '2')

        # * He enters "=a1+A2" in A3.  When he moves away, he sees "3"
        self.enter_cell_text(1, 3, '=11+22')
        self.click_on_cell(2, 4)
        self.wait_for_cell_value(1, 3, '33')

        # When he edits the cell again, he is presented with the formula as he entered it
        self.open_cell_for_editing(1, 3)
        self.wait_for_cell_editor_content('=11+22')

        # He moves the cursor left and right while editing and the edited cell does not move
        print('checking arrow keys')
        self.human_key_press(Keys.LEFT)
        self.human_key_press(Keys.RIGHT)
        self.assert_editing_cell(1, 3)

        self.open_cell_for_editing(3, 3)
        self.human_key_press(Keys.LEFT)
        self.human_key_press(Keys.LEFT)
        self.assert_editing_cell(3, 3)

        # * He enters "=a1+A2" (NB case!) in A4.  When he moves away, he sees "3"
        self.enter_cell_text(1, 4, '=a1+A2')
        self.click_on_cell(2, 5)
        self.wait_for_cell_value(1, 4, '3')

        # When he edits the cell again, he is presented with the formula as he entered it
        self.open_cell_for_editing(1, 4)
        self.wait_for_cell_editor_content('=a1+A2')


    def test_new_sheet_not_logged_in(self):
        # * Harold goes to /new_sheet without logging in
        # * He gets redirected to the login page
        self.assert_sends_to_login_page(Url.NEW_SHEET)

        # * He logs in
        self.login(already_on_login_page=True)
        # * ... and gets take to a new sheet
        url = urlparse(self.browser.current_url)
        self.assertEquals(url.netloc, Url.ROOT)
        self.assertRegexpMatches(url.path, '/user/%s/sheet/[0-9]+/' % (self.get_my_username(),))


    @snapshot_on_error
    def test_access_sheet_with_incorrect_user_id(self):
        ## Create sheet as user 1, for the rest of the test
        harriet = self.get_my_usernames()[1]
        harold = self.get_my_username()
        sheet_id = self.login_and_create_new_sheet(username=harriet)
        self.logout()
        harolds_broken_sheet_url = '/user/%s/sheet/%s' % (harold, sheet_id)

        # Before logging in, Harold tries to access one of Harriet's sheets
        # using the wrong direct URL, with his username but the correct sheet ID.
        # He gets a 404
        self.assert_HTTP_error(harolds_broken_sheet_url, 404)

        # After logging in, Harold tries to access one of Harriet's sheets
        # using the wrong direct URL, with his username but the correct sheet ID.
        # He gets a 404.
        self.login(username=harold)
        self.assert_HTTP_error(harolds_broken_sheet_url, 404)
