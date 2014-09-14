# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#
from __future__ import with_statement

from textwrap import dedent

import key_codes
from functionaltest import FunctionalTest, snapshot_on_error


class Test_2521_CodeEditor(FunctionalTest):

    def test_code_editor_tabs_and_indents(self):
        # * Harold wants an editor with syntax coloring and other good stuff
        #   instead of a boring textarea

        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notes that the code editor is an Ace editor (!)
        self.assertTrue(
            self.selenium.is_element_present('css=#id_usercode.ace_editor'),
            'editor component not present'
        )

        # * He plays around with the code editor and discovers that
        original_code = self.get_usercode()
        self.selenium.get_eval('window.editor.focus()')
        self.human_key_press(key_codes.LETTER_A)
        self.human_key_press(key_codes.ENTER)
        self.human_key_press(key_codes.TAB)
        self.human_key_press(key_codes.LETTER_B)
        self.human_key_press(key_codes.ENTER)

        # ... tabs are converted to 4 spaces, and it autoindents
        four_spaces = '    '
        autoindent = four_spaces
        expected_code_after_typing = 'a\n%sb\n%s%s' % (four_spaces, autoindent, original_code)
        self.wait_for_usercode_editor_content(expected_code_after_typing)

        # ... undo works
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_Z)
        expected_code_after_undo = 'a\n%sb%s' % (four_spaces, original_code)
        self.wait_for_usercode_editor_content(expected_code_after_undo)

        # ... and redo works
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_Y)
        self.wait_for_usercode_editor_content(expected_code_after_typing)


    @snapshot_on_error
    def test_code_editor_shows_errors(self):
        # * Harold makes mistakes when writing Python and wants Dirigible to
        #   tell him about them so he can fix them

        error_locator = 'css=div.ace_gutter-cell.ace_error'

        def assert_error(line, message):
            self.wait_for_element_to_appear(error_locator)
            self.assertEquals(self.get_text(error_locator), str(line))
            self.assertEquals(
                self.selenium.get_attribute('%s@title' % error_locator),
                message
            )

        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters a value into the grid
        self.enter_cell_text(1, 1, 'herrrroooo')

        original_usercode = self.get_usercode()

        # * He enters some code that creates a syntax error
        self.prepend_usercode('import sys:')

        # ... and notes that an error appears in the code editor, and the value
        # in the grid is grey because the load_constants in the usercode was
        # never executed.
        self.wait_for_cell_shown_formula(1, 1, 'herrrroooo')

        assert_error(1, 'Syntax error at character 11')

        # * He refreshes the page, just because he's ornery and notes that the
        # grid is intact and the error is marked

        self.refresh_sheet_page()

        self.assert_cell_shown_formula(1, 1, 'herrrroooo')

        assert_error(1, 'Syntax error at character 11')

        # * He deletes his mistake and, the error indicator goes away and the
        #   text ungreys
        self.enter_usercode(original_usercode)
        self.wait_for_cell_value(1, 1, 'herrrroooo')
        self.wait_for_element_presence(error_locator, False)

        # * Not satisfied, he tries a different type of error, this one after
        # the usercode loads the constants.
        original_usercode_lines = len(original_usercode.split('\n'))
        self.append_usercode('x = newvalue')

        # Once again, he notes that his grid survives, an error appears in the
        # right place.  However, this time the cell value is not grey.
        self.wait_for_cell_value(1, 1, 'herrrroooo')
        assert_error(
            original_usercode_lines + 1,
            u"NameError: name \u2019newvalue\u2019 is not defined"
        )


    def get_editor_selected_range(self):
        return eval(
            self.selenium.get_eval("""
                (function() {
                    var selection = window.editor.getSelectionRange();
                    return (
                        selection.start.column + ", " + selection.start.row + ", " +
                        selection.end.column + ", " + selection.end.row
                    );
                })()
            """)
        )


    def assert_editor_line_visible(self, line):
        self.assertTrue(int(self.selenium.get_eval("window.editor.getFirstVisibleRow()")) < line)
        self.assertTrue(int(self.selenium.get_eval("window.editor.getLastVisibleRow()")) > line)


    @snapshot_on_error
    def test_code_editor_find_function(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # He enters some long and complicated usercode, which contains the string "123" at a well-known place,
        # and doesn't hit "save".
        code = ""
        for i in range(100):
            code += "a\n"
        code += "abc123def"
        for i in range(100):
            code += "a\n"

        self.enter_usercode(code, commit_change=False)

        # He hits ^F, and types 123 into the resulting dialog.
        self.selenium.answer_on_next_prompt("123")
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_F)

        # The editor jumps to the "123" bit and selects it.
        self.assertEquals(self.get_editor_selected_range(), (3, 100, 6, 100))

        # The line is, of course, visible.
        self.assert_editor_line_visible(100)



    @snapshot_on_error
    def test_code_editor_go_to_line_function(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # He enters some long and complicated usercode and doesn't hit "save".
        code = ""
        for i in range(200):
            code += "a\n"

        self.enter_usercode(code, commit_change=False)

        # He hits ^L, and types 100 into the resulting dialog.
        self.selenium.answer_on_next_prompt("100")
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_L)

        # The editor jumps to line 100
        self.assertEquals(self.get_editor_selected_range(), (0, 99, 0, 99))

        # The line is, of course, visible.
        self.assert_editor_line_visible(100)
