# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, snapshot_on_error
import key_codes


class Test_2581_FormulaBar(FunctionalTest):

    def wait_for_formula_bar_enabled(self):
        self.wait_for(
            self.is_formula_bar_enabled,
            lambda: 'formula bar to enable',
        )

    def wait_for_formula_bar_disabled(self):
        self.wait_for(
            lambda: not self.is_formula_bar_enabled(),
            lambda: 'formula bar to disable',
        )

    def test_formula_bar(self):
        # Harold lacks the mental egg-juggling capacity of a Real Programmer,
        # and wants to be reminded of relevant state as he examines his
        # spreadsheet.

        # * He logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He observes that there is a single-line text box above the grid.
        bar_bounds = self.get_element_bounds(self.get_formula_bar_locator())

        grid_locator = "id=id_grid"
        grid_bounds = self.get_element_bounds(grid_locator)

        self.assertTrue(
            abs(bar_bounds.left - grid_bounds.left) < 50,
            "Grid and formula bar not roughly horizontally aligned"
        )
        self.assertTrue(
            abs(bar_bounds.width - grid_bounds.width) < 100,
            "Grid and formula bar not roughly the same width"
        )
        self.assertTrue(
            bar_bounds.top + bar_bounds.height < grid_bounds.top,
            "Formula bar not above grid"
        )

        # * He notes that cell A1 is active, and he can edit the formula bar,
        #   which is empty
        ## NB click doesn't work here -- it's for links and buttons only.
        ## Which makes it strange that it works with cells!
        self.wait_for_cell_to_become_active(1, 1)
        self.wait_for_formula_bar_enabled()
        self.click_formula_bar()
        self.assertTrue(
            self.is_element_focused('id=%s' % (self.get_formula_bar_id(),)))
        self.wait_for_formula_bar_contents("")

        # * As he starts to type "456", he observes that the cell editor
        #   updates with each keystroke.
        self.human_key_press(key_codes.NUMBER_4)
        # workaround for defect T2708
        #self.wait_for_cell_editor_content("4")

        self.human_key_press(key_codes.NUMBER_5)
        self.wait_for_cell_editor_content("45")

        self.human_key_press(key_codes.NUMBER_6)
        self.wait_for_cell_editor_content("456")

        # * He then edits cell A2
        self.open_cell_for_editing(1, 2)
        self.wait_for_cell_to_enter_edit_mode(1, 2)

        # and notes that the formula bar becomes empty
        self.wait_for_formula_bar_contents("")

        # while cell A1 still contains "456".
        self.wait_for_cell_value(1, 1, "456")

        # * He types "123"; as he does so, the contents of the formula bar
        #   update with each keystroke.
        self.human_key_press(key_codes.NUMBER_1)
        self.wait_for_formula_bar_contents("1")

        self.human_key_press(key_codes.NUMBER_2)
        self.wait_for_formula_bar_contents("12")

        self.human_key_press(key_codes.NUMBER_3)
        self.wait_for_formula_bar_contents("123")

        # * He edits cell A1, and notes that both the cell and the formula bar
        #   read "456".
        self.open_cell_for_editing(1, 1)
        self.wait_for_cell_editor_content("456")
        self.wait_for_formula_bar_contents("456")

        # * Harold edits A3, and enters "78".
        self.open_cell_for_editing(1, 3)
        self.human_key_press(key_codes.NUMBER_7)
        self.human_key_press(key_codes.NUMBER_8)

        #   The formula bar shows 78.
        self.wait_for_formula_bar_contents("78")

        # * He clicks in the formula bar, hits the "end" key, and enters "90".
        self.click_formula_bar()
        self.human_key_press(key_codes.END)
        self.human_key_press(key_codes.NUMBER_9)
        self.human_key_press(key_codes.NUMBER_0)

        #   The cell editor and the formula bar both show 7890.
        self.wait_for_cell_editor_content("7890")
        self.assert_formula_bar_contains("7890")

        # * Harold clicks on A4,
        self.click_on_cell(1, 4)

        #   and then wonders whether he can commit changes from the formula bar
        #   without click to a cell, so he clicks on the formula bar,
        self.click_formula_bar()

        #  types "321<ENTER>".
        self.human_key_press(key_codes.NUMBER_3)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.ENTER)

        #    and is delighted to see the cell update.
        self.wait_for_cell_value(1, 4, "321")


    @snapshot_on_error
    def test_formula_bar_remains_enabled_at_all_times(self):

        # Harry logs in and creates a new sheet.
        self.login_and_create_new_sheet()

        # * the formula bar is enabled because a cell has focus
        self.wait_for_formula_bar_enabled()
        self.wait_for_cell_to_become_active(1, 1)

        # * he clicks in the output pane
        #  the formula bar remains enabled
        self.selenium.click('id=id_console')
        self.wait_for_formula_bar_enabled()

        # * he clicks in the usercode
        #  the formula bar remains enabled
        self.selenium.get_eval('window.editor.focus()')
        self.wait_for_formula_bar_enabled()

        # * he clicks in the sheet title
        #  the formula bar remains enabled
        self.selenium.click('id=id_sheet_name')
        self.wait_for_formula_bar_enabled()

        # He presses escape to cancel the sheet title edit
        self.human_key_press(key_codes.ESCAPE)

        #  * He clicks in the formula bar
        self.click_formula_bar()

        #  and types "321<ENTER>".
        self.human_key_press(key_codes.NUMBER_3)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.ENTER)

        # and is delighted to see cell A1 update.
        self.wait_for_cell_value(1, 1, "321")
