# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest, snapshot_on_error


class Test_2545_PageResizeBehaviour(FunctionalTest):

    @snapshot_on_error
    def test_splitters(self):
        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # He notes that there are splitter bars
        self.assertTrue(self.selenium.is_element_present('css=.hsplitbar'))
        self.assertTrue(self.selenium.is_element_present('css=.vsplitbar'))

        # He uses the vertical split bar to resize the grid to its minimum width
        self.selenium.drag_and_drop('css=.vsplitbar', '-4000, 0')
        self.assertAlmostEquals(self.selenium.get_element_width('id=id_left_column'), 0, delta=5)
        # and then increases its width a bit
        self.selenium.drag_and_drop('css=.vsplitbar', '40, 0')
        self.assertAlmostEquals(self.selenium.get_element_width('id=id_left_column'), 40, delta=5)

        # He uses the horizontal split bar to shrink the console
        self.selenium.drag_and_drop('css=.hsplitbar', '0, 2000')
        self.assertAlmostEquals(self.selenium.get_element_height('id=id_console_wrap'), 0, delta=5)
        # and then increases its height a bit
        self.selenium.drag_and_drop('css=.hsplitbar', '0, -20')
        self.assertAlmostEquals(self.selenium.get_element_height('id=id_console_wrap'), 20, delta=5)

        # He notes that his splitter positions are restored when he reloads the page
        self.refresh_sheet_page()
        self.wait_for_grid_to_appear()
        self.assertAlmostEquals(self.selenium.get_element_width('id=id_left_column'), 40, delta=5)
        self.assertAlmostEquals(self.selenium.get_element_height('id=id_console_wrap'), 20, delta=5)

        # He uses the vertical split bar to resize the right-hand column to its minimum width
        self.selenium.drag_and_drop('css=.vsplitbar', '4000, 0')
        self.assertAlmostEquals(self.selenium.get_element_width('id=id_right_column'), 0, delta=5)
        # and then increases its width a bit
        self.selenium.drag_and_drop('css=.vsplitbar', '-40, 0')
        self.assertAlmostEquals(self.selenium.get_element_width('id=id_right_column'), 40, delta=5)

        # He uses the horizontal split bar to shrink the editor to zero size, and notes that it disappears
        self.selenium.drag_and_drop('css=.hsplitbar', '0, -2000')
        self.wait_for_element_visibility('id=id_usercode', False)

        # He uses the horizontal split bar to make the editor 25px high, and notes that it is still hidden
        self.selenium.drag_and_drop('css=.hsplitbar', '0, 25')
        self.wait_for_element_visibility('id=id_usercode', False)

        # He uses the horizontal split bar to give the editor and its margins 50px of space, and notes
        # that it is visible and small
        self.selenium.drag_and_drop('css=.hsplitbar', '0, 25')
        self.wait_for_element_visibility('id=id_usercode', True)
        self.assertAlmostEquals(self.selenium.get_element_height('id=id_usercode'), 40, delta=5)


    @snapshot_on_error
    def test_grid_resize(self):
        # Harold logs in a creates a new sheet.
        self.login_and_create_new_sheet()

        # He sees that the bottom of the grid is a specific distance from the bottom of the window,
        # and that the top of the grid is a specific distance from the top of the window.  He notes
        # those distances down.
        grid_bounds = self.get_element_bounds("id=id_grid")
        browser_page_height = int(self.selenium.get_eval("window.document.body.clientHeight"))
        browser_page_width = int(self.selenium.get_eval("window.document.body.clientWidth"))
        original_distance_to_bottom = browser_page_height - grid_bounds.bottom
        original_distance_to_top = grid_bounds.top

        # He resizes the window.
        self.selenium.get_eval("window.resizeTo(%s, %s)" % (browser_page_width - 10, browser_page_height - 10))

        # He notes that the grid is still the same distances from the top and the bottom of the
        # window.
        def get_distance_to_bottom():
            new_grid_bounds = self.get_element_bounds("id=id_grid")
            browser_page_height = int(self.selenium.get_eval("window.document.body.clientHeight"))
            return browser_page_height - new_grid_bounds.bottom
        self.wait_for(
            lambda: get_distance_to_bottom() == original_distance_to_bottom,
            lambda: "Distance to bottom to become %s (was %s)" % (original_distance_to_bottom, get_distance_to_bottom())
        )

        def get_distance_to_top():
            return self.get_element_bounds("id=id_grid").top
        self.wait_for(
            lambda: get_distance_to_top() == original_distance_to_top,
            lambda: "Distance to top to become %s (was %s)" % (original_distance_to_top, get_distance_to_top())
        )
