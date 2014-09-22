# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

from functionaltest import FunctionalTest
import key_codes


class Test_2633_CursorKeysMoveAroundGrid(FunctionalTest):

    def get_cell_editor_cursor_position(self):
        try:
            selection_start = int(self.selenium.get_eval("window.$('%s').caret().start" % (self.get_cell_editor_css(),)))
            selection_end = int(self.selenium.get_eval("window.$('%s').caret().end" % (self.get_cell_editor_css(),)))
        except ValueError:
            return None
        self.assertEquals(selection_start, selection_end, "Time to refactor?")
        return selection_start


    def assert_editing_cell_at_position(self, col, row, position):
        self.assert_cell_is_current_and_is_editing(col, row)
        self.assertEquals(position, self.get_cell_editor_cursor_position())



    def test_navigate_with_cursor_keys(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        self.selenium.get_eval('window.$(".grid-canvas").focus();')

        # * He clicks on a random cell
        self.click_on_cell(3, 4)

        #   and it is clear to him that he is not in edit mode
        #   ie focus is not captured by the input box
        self.assert_cell_is_current_but_not_editing(3, 4)

        # * He uses the LRUD cursor keys and sees he is navigating around
        #   the grid
        self.human_key_press(key_codes.LEFT)
        self.assert_cell_is_current_but_not_editing(2, 4)

        self.human_key_press(key_codes.UP)
        self.assert_cell_is_current_but_not_editing(2, 3)

        self.human_key_press(key_codes.RIGHT)
        self.assert_cell_is_current_but_not_editing(3, 3)

        self.human_key_press(key_codes.DOWN)
        self.assert_cell_is_current_but_not_editing(3, 4)

        # * He finds that tab and shift-tab also move right and left
        self.human_key_press(key_codes.TAB)
        self.assert_cell_is_current_but_not_editing(4, 4)

        with self.key_down(key_codes.SHIFT):
            self.human_key_press(key_codes.TAB)
        self.assert_cell_is_current_but_not_editing(3, 4)

        # * He tries to go past the top row and gets blocked
        self.click_on_cell(5,1)
        self.human_key_press(key_codes.UP)
        self.assert_cell_is_current_but_not_editing(5, 1)
        #   Same for leftmost column
        self.click_on_cell(1,5)
        self.human_key_press(key_codes.LEFT)
        self.assert_cell_is_current_but_not_editing(1, 5)

        # * He presses down to scroll off the bottom of the current screen
        #   and notices the grid scrolls down with him
        self.click_on_cell(1,1)
        MAXROW = 50
        for expected_row in range(1, MAXROW):
            self.assert_cell_is_current_but_not_editing(1, expected_row)
            self.assert_cell_visible(1, expected_row)
            self.human_key_press(key_codes.DOWN)

        #   he sees it also works when he goes back up again
        for expected_row in range(MAXROW, 1, -1):
            self.assert_cell_is_current_but_not_editing(1, expected_row)
            self.assert_cell_visible(1, expected_row)
            self.human_key_press(key_codes.UP)


        #   He goes to the edge of the screen on the right
        #   and notices the grid scrolls right with him.
        self.click_on_cell(1,1)
        MAXCOL = 20
        for expected_col in range(1, MAXCOL):
            self.assert_cell_is_current_but_not_editing(expected_col, 1)
            self.assert_cell_visible(expected_col, 1)
            self.human_key_press(key_codes.RIGHT)

        #   he sees it also works when he goes back left again
        for expected_col in range(MAXCOL, 1, -1):
            self.assert_cell_is_current_but_not_editing(expected_col, 1)
            self.assert_cell_visible(expected_col, 1)
            self.human_key_press(key_codes.LEFT)

        def get_bottom_row():
            # assumes the grid is scrolled up to row 1 to begin
            row = 1
            while True:
                if not self.is_cell_visible(1, row):
                    return row
                row += 1

        # * He clicks in the middle of the visible grid, then
        #   tries page up, but since the grid is already scrolled
        #   all the way up, nothing happens
        self.click_on_cell(5, 5)
        self.human_key_press(key_codes.PAGE_UP)
        self.assertEquals(self.get_viewport_top(), 1)
        self.assert_cell_is_current_but_not_editing(5, 5)

        # * He tries pageDown and notes to his delight
        #   that the grid scrolls down one page
        _, old_row = self.get_current_cell()
        old_distance_from_top = old_row - self.get_viewport_top()
        old_bottom_row = get_bottom_row()
        page_size = self.get_viewport_bottom() - self.get_viewport_top() - 1
        self.human_key_press(key_codes.PAGE_DOWN)

        # correct new current cell is selected:
        self.assert_cell_is_current_but_not_editing(
            5, old_row + page_size
        )

        # grid is scrolled to correct place:
        _, new_row = self.get_current_cell()
        new_distance_from_top = new_row - self.get_viewport_top()
        self.assertEquals(new_distance_from_top, old_distance_from_top)

        # * He uses pageUp to return to the top of the grid
        _, row = self.get_current_cell()
        self.human_key_press(key_codes.PAGE_UP)
        self.assert_cell_is_current_but_not_editing(5, 5)

        # grid is scrolled to correct place:
        self.assertEquals(self.get_viewport_top(), 1)

        # * He selects a cell right at the bottom of the grid.
        self.click_on_cell(5, 990)

        # * He hits pageDown a bunch of times and discovers that he
        #   reaches a stable last row
        pageDowns = 0
        last_bottom_row = None
        hit_bottom = False
        while pageDowns < 6:
            current_bottom_row = self.get_viewport_bottom()
            if current_bottom_row == last_bottom_row:
                hit_bottom = True
                break
            last_bottom_row = current_bottom_row
            self.human_key_press(key_codes.PAGE_DOWN)
            pageDowns += 1
        self.assertTrue(hit_bottom, "Didn't hit bottom after paging down")


        # * He hits pageUp and notes that the currently-selected cell
        #   remains in the same place within the visible grid
        _, old_row = self.get_current_cell()
        old_distance_from_top = old_row - self.get_viewport_top()
        old_bottom_row = get_bottom_row()
        page_size = self.get_viewport_bottom() - self.get_viewport_top() - 1
        self.human_key_press(key_codes.PAGE_UP)

        _, new_row = self.get_current_cell()
        new_distance_from_top = new_row - self.get_viewport_top()
        self.assertEquals(new_distance_from_top, old_distance_from_top)

        # * Amazed at the instinctiveness of Dirigible's grid navigation,
        #   he wonders whether ctrl+home might take him back to the top left
        #   and is well pleased when it does
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.HOME)
        self.assert_cell_is_current_but_not_editing(1, 1)
        self.assert_cell_visible(1, 1)

        # * Ctrl+end takes him to the bottommost rightest cell also.
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.END)
        self.assert_cell_is_current_but_not_editing(52, 1000)
        self.assert_cell_visible(52, 1000)


    def test_formula_bar_contents_should_follow_current_cell(self):
        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # He enters some data.
        self.enter_cell_text(1, 1, "=4567")
        self.enter_cell_text(2, 2, "='B2'")

        # He moves around the grid using the cursor keys and the mouse and notes
        # that the contents of the formula bar always reflect the contents of the
        # selected cell.
        self.click_on_cell(1, 1)
        self.wait_for_formula_bar_contents("=4567")
        self.click_on_cell(1, 2)
        self.wait_for_formula_bar_contents("")
        self.click_on_cell(2, 2)
        self.wait_for_formula_bar_contents("='B2'")
        self.click_on_cell(2, 1)
        self.wait_for_formula_bar_contents("")

        self.human_key_press(key_codes.LEFT)
        self.wait_for_formula_bar_contents("=4567")
        self.human_key_press(key_codes.DOWN)
        self.wait_for_formula_bar_contents("")
        self.human_key_press(key_codes.RIGHT)
        self.wait_for_formula_bar_contents("='B2'")
        self.human_key_press(key_codes.UP)
        self.wait_for_formula_bar_contents("")

        # While an empty cell is selected, he clicks in the formula bar.
        self.click_on_cell(2, 1)
        self.wait_for_formula_bar_contents("")
        self.click_formula_bar()

        # He notes that the cell shifts into edit mode (though it remains empty)
        full_editor_locator = self.get_cell_editor_locator(2, 1)
        self.wait_for(
            lambda : self.is_element_present(full_editor_locator),
            lambda : "Editor at (%s, %s) to be present" % (2, 1),
        )
        self.wait_for_cell_editor_content("")

        # He types into the formula bar and hits return.
        self.human_key_press(key_codes.NUMBER_7)

        # He sees his change applied.
        # (commented out as workaround for defect T2708)
        #self.wait_for_cell_value(2, 1, "7")

        self.human_key_press(key_codes.NUMBER_8)
        self.human_key_press(key_codes.ENTER)
        self.wait_for_cell_value(2, 1, "78")

        # He moves over to a populated cell and clicks in the formula bar
        self.click_on_cell(1, 1)
        self.wait_for_formula_bar_contents("=4567")
        self.click_formula_bar()

        # He notes that the cell shifts into edit mode and shows the formula.
        full_editor_locator = self.get_cell_editor_locator(1, 1)
        self.wait_for(
            lambda : self.is_element_present(full_editor_locator),
            lambda : "Editor at (%s, %s) to be present" % (1, 1),
        )
        self.wait_for_cell_editor_content("=4567")

        # He changes the contents of the formula bar and hits ENTER.
        self.human_key_press(key_codes.NUMBER_9)
        self.human_key_press(key_codes.NUMBER_0)
        self.human_key_press(key_codes.ENTER)

        # He sees that change applied too.
        self.wait_for_cell_value(1, 1, "456790")


    def test_down_and_enter_keys_commit_edit_and_move_current_cell_down(self):
        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # He enters some data into cell A1, and hits the down arrow.
        self.open_cell_for_editing(1, 1)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)
        self.human_key_press(key_codes.DOWN)

        # His change is committed into A1
        self.wait_for_cell_value(1, 1, "123")

        # A2 is the current cell.
        self.assert_cell_is_current_but_not_editing(1, 2)

        # He enters some data into cell B1, and hits the enter key.
        self.open_cell_for_editing(2, 1)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)
        self.human_key_press(key_codes.ENTER)

        # His change is committed into B1
        self.wait_for_cell_value(2, 1, "123")

        # B2 is the current cell.
        self.assert_cell_is_current_but_not_editing(2, 2)

        # He starts editing C1 in the formula bar and enters some data finishing with an enter.
        self.click_on_cell(3, 1)
        self.click_formula_bar()
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)
        self.human_key_press(key_codes.ENTER)

        # His change is committed into C1
        self.wait_for_cell_value(3, 1, "123")

        # C2 is the current cell.
        self.assert_cell_is_current_but_not_editing(3, 2)

        # He starts editing D1 in the formula bar and enters some data finishing with an down arrow.
        self.click_on_cell(4, 1)
        self.click_formula_bar()
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)
        self.human_key_press(key_codes.DOWN)

        # His change is *not* committed, and the current cell remains D1.
        self.wait_for_cell_to_become_active(4, 1)
        self.assertTrue(self.is_element_focused(self.get_formula_bar_locator()))



    def test_begin_typing_enters_edit_mode(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He clicks on a cell and begins typing
        self.click_on_cell(2, 3)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * He is pleased to see that the cell he clicked on is in edit mode
        self.wait_for_cell_to_enter_edit_mode(2, 3)

        #   .. and contains the stuff he typed
        self.wait_for_cell_editor_content('123')
        #   .. as does the formula bar
        self.wait_for_formula_bar_contents('123')

        # * He enters some other data into a different cell,
        #   clicks away from it and then back again
        self.enter_cell_text(4, 5, '="some other data"')
        self.click_on_cell(1, 1)
        self.click_on_cell(4, 5)

        # * He presses some random keys and notes that they don't cause
        #   the cell to go into edit mode and that the original content
        #   is unchanged
        self.human_key_press(key_codes.CTRL)
        self.assert_cell_is_current_but_not_editing(4, 5)

        self.human_key_press(key_codes.SHIFT)
        self.assert_cell_is_current_but_not_editing(4, 5)

        # * He clicks on the original cell and presses F2.
        self.click_on_cell(2, 3)

        # * He types some text and notes that it appears after the original text
        self.human_key_press(key_codes.F2)
        self.wait_for_cell_editor_content('123')
        self.human_key_press(key_codes.NUMBER_5)
        self.human_key_press(key_codes.NUMBER_1)
        self.wait_for_cell_editor_content('12351')

        # * He clicks on another cell with content and just starts typing.
        # * He notes that the previous content is replaced by what he just typed
        self.click_on_cell(4, 5)
        self.assert_cell_is_current_but_not_editing(4, 5)
        self.human_key_press(key_codes.NUMBER_5)
        self.wait_for_cell_to_enter_edit_mode(4, 5)
        self.wait_for_cell_editor_content('5')


    def test_cursor_keys_while_editing(self):
        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # He enters some data into cell B2
        test_cell = 2, 2
        self.open_cell_for_editing(*test_cell)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # He hits the left arrow, and the cursor moves around within his entered data
        for expected_cursor_position in (2, 1, 0):
            self.human_key_press(key_codes.LEFT)
            self.assert_editing_cell_at_position(test_cell[0], test_cell[1], expected_cursor_position)

        # When he tries to move off the left-hand side of the input field, he is stopped.
        self.human_key_press(key_codes.LEFT)
        self.assert_editing_cell_at_position(test_cell[0], test_cell[1], 0)

        # He hits the right arrow, and the cursor moves around within his entered data
        for expected_cursor_position in (1, 2, 3):
            self.human_key_press(key_codes.RIGHT)
            self.assert_editing_cell_at_position(test_cell[0], test_cell[1], expected_cursor_position)

        # When he tries to move off the right-hand side of the input field, he is stopped.
        self.human_key_press(key_codes.RIGHT)
        self.assert_editing_cell_at_position(test_cell[0], test_cell[1], 3)

        # He hits the up arrow, and sees his changes committed and the current cell move up.
        self.human_key_press(key_codes.UP)
        self.wait_for_cell_value(2, 2, "123")
        self.assert_cell_is_current_but_not_editing(2, 1)

        # He goes back into edit mode on cell B2, enters some data, then hits the down
        # arrow.  His changes are committed and the current cell moves down.
        self.open_cell_for_editing(*test_cell)
        self.human_key_press(key_codes.NUMBER_4)
        self.human_key_press(key_codes.DOWN)
        self.wait_for_cell_value(2, 2, "1234")
        self.assert_cell_is_current_but_not_editing(2, 3)


    def test_editor_font_size_is_consistent(self):
        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # * He enters text into a cell
        self.enter_cell_text(1, 1, "foo")

        # * He gets out a ruler and measures the text height
        cell_font_size_expression = "window.$('%s').css('font-size')" % (self.get_cell_css(1, 1),)
        cell_font_size = self.selenium.get_eval(cell_font_size_expression)

        # * He edits the cell again, and measures the height again while still editing
        self.open_cell_for_editing(1, 1)
        editor_font_size_expression = "window.$('%s').css('font-size')" % (self.get_cell_editor_css(),)
        editor_font_size = self.selenium.get_eval(editor_font_size_expression)

        # * He is pleased to discover the two measured heights are the same.
        self.assertTrue(cell_font_size.endswith('px'))
        self.assertEquals(cell_font_size, editor_font_size)


    def test_enter_single_character(self):
        ## This is to test for regression of a particular re-occuring bug that
        ## leads to single characters not committing properly.

        # Harold logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # He clicks on cell A1
        self.click_on_cell(1, 1)

        # He types "1"
        self.human_key_press(key_codes.NUMBER_1)

        # He hits <ENTER>
        self.human_key_press(key_codes.ENTER)

        # The number "1" commits properly and appears in the cell.
        self.wait_for_cell_value(1, 1, "1")
