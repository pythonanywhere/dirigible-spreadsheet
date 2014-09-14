# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest


class Test_2558_MoreCellsByDefault(FunctionalTest):

    def test_more_cells_by_default(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notes that the sheet he is presented with has
        #   an elegant sufficiency of rows and columns (1000 rows and 702
        #   (up to ZZ) columns)
        self.scroll_cell_row_into_view(1, 1000)

        row_list_xpath = '//div[contains(@class, "slick-row") and @row=999]'
        row_count = self.selenium.get_xpath_count(row_list_xpath)
        self.assertEquals(row_count, 1, 'fewer than 1000 rows')

        self.scroll_cell_row_into_view(52, 1)
        column_list_xpath = '//div[@class="slick-cell c52"]'

        column_count = self.selenium.get_xpath_count(column_list_xpath)
        self.assertTrue(column_count >= 1, 'fewer than AZ columns')

        self.scroll_cell_row_into_view(1, 1)
        # * The last cell on the grid accepts input as expected
        self.enter_cell_text(52, 1000, 'end of the sheet')

        # * He notes that, since he just typed on the bottom row,
        #   the cell stays in edit mode, so he has to click away
        #   to finish the edit
        self.click_on_cell(51, 999)
        self.wait_for_cell_value(52, 1000, 'end of the sheet')
