# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest
import key_codes

class Test_2652_CommitCellOnBlur(FunctionalTest):

    def test_blur_cell_saves_cell_contents(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He edits a cell and types, but doesn't press enter
        self.open_cell_for_editing(1, 2)
        self.type_into_cell_editor_unhumanized("='hello'")

        # * He clicks on another cell
        self.click_on_cell(2, 3)
        # * and notes that his edit has been commited
        self.wait_for_cell_value(1, 2, "hello")

        # * He types into the new cell, again without pressing enter
        self.open_cell_for_editing(2, 3)
        self.type_into_cell_editor_unhumanized("='goodbye'")

        # * and clicks away to something that isn't a cell.
        self.selenium.click('id=id_console')
        # * the second edit is also committed
        self.wait_for_cell_value(2, 3, "goodbye")


    def test_blur_formula_bar_saves_cell_contents(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He double-clicks on a cell
        self.open_cell_for_editing(1, 2)

        # and types into the formula bar, but doesn't press enter
        self.click_formula_bar()
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * He clicks on another cell
        self.click_on_cell(2, 3)
        # * and notes that his edit has been commited
        self.wait_for_cell_value(1, 2, "123")

        # * He edits the new cell, again using the formula bar and without pressing enter
        self.open_cell_for_editing(2, 3)
        self.click_formula_bar()
        self.human_key_press(key_codes.NUMBER_4)
        self.human_key_press(key_codes.NUMBER_5)
        self.human_key_press(key_codes.NUMBER_6)

        # * and clicks away
        self.selenium.click('id=id_console')

        # * the second edit is also committed
        self.wait_for_cell_value(2, 3, "456")
