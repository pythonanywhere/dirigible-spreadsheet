# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent
from time import sleep

from functionaltest import FunctionalTest
import key_codes


class Test_2689_DontClearCellEditorOrFormulaBarWhenRecalcsHitClient(FunctionalTest):

    def test_cell_editor_not_cleared(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He creates a sheet that will take at least 5 seconds to recalc.
        self.append_usercode(dedent("""
            import time
            time.sleep(25)
        """))

        # * He waits for the first recalc to complete
        self.wait_for_spinner_to_stop(timeout_seconds=30)

        # * He enters 1 in cell A1
        self.enter_cell_text(1, 1, "1")

        # * Without waiting for the recalc to complete, he edits cell A2 and types "test" but doesn't hit return.
        self.open_cell_for_editing(1, 2)
        self.wait_for_cell_to_enter_edit_mode(1, 2)
        self.type_into_cell_editor_unhumanized("test")

        # * He waits for more than 25 seconds, and notes that the recalc ends.
        sleep(25)
        self.wait_for_spinner_to_stop(timeout_seconds=20)

        # * The cell editor still contains "test"
        self.wait_for_cell_editor_content("test")


    def test_formula_bar_not_cleared(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He creates a sheet that will take at least 5 seconds to recalc.
        self.append_usercode(dedent("""
            import time
            time.sleep(25)
        """))

        # * He waits for the first recalc to complete
        self.wait_for_spinner_to_stop(timeout_seconds=30)

        # * He enters 1 in cell A1
        self.enter_cell_text(1, 1, "1")

        # * Without waiting for the recalc to complete, he edits cell A2 and types "123" into the formula
        #   bar, but doesn't hit return.
        self.open_cell_for_editing(1, 2)
        self.wait_for_cell_to_enter_edit_mode(1, 2)
        self.click_formula_bar()
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)
        self.human_key_press(key_codes.NUMBER_3)

        # * He waits for more than 25 seconds, and notes that the recalc ends.
        sleep(25)
        self.wait_for_spinner_to_stop(timeout_seconds=20)

        # * The formula bar still contains "123"
        self.assert_formula_bar_contains("123")
