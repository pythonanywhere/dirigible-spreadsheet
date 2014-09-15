# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from selenium.webdriver.common.keys import Keys
from textwrap import dedent

from functionaltest import FunctionalTest, snapshot_on_error


class Test_2521_CodeEditor(FunctionalTest):

    def test_code_editor_tabs_and_indents(self):
        # * Harold wants an editor with syntax coloring and other good stuff
        #   instead of a boring textarea

        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notes that the code editor is an Ace editor (!)
        self.assertTrue(
            self.is_element_present('css=#id_usercode.ace_editor'),
            'editor component not present'
        )

        # * He plays around with the code editor and discovers that
        # tabs are converted to 4 spaces, and it autoindents

        original_code = self.get_usercode()
        self.get_element('id=id_usercode').click()
        self.human_key_press('a')
        self.human_key_press('\n')
        self.human_key_press(Keys.TAB)
        self.human_key_press('b')
        self.human_key_press('\n')
        self.human_key_press('c')
        self.human_key_press('\n')

        four_spaces = '    '
        autoindent = four_spaces
        expected_code_after_typing = (
            '{original_code}a\n'
            '{four_spaces}b\n'
            '{autoindent}c\n'
        ).format(
            original_code=original_code,
            four_spaces=four_spaces,
            autoindent=autoindent
        )
        self.wait_for_usercode_editor_content(expected_code_after_typing)

        # ... undo works
        with self.key_down(Keys.CONTROL):
            self.human_key_press('z')

        with self.key_down(Keys.CONTROL):
            self.human_key_press('z')

        expected_code_after_undo = (
            '{original_code}a\n'
            '{four_spaces}b\n'
        ).format(
            original_code=original_code,
            four_spaces=four_spaces,
        )
        self.wait_for_usercode_editor_content(expected_code_after_undo)

        # ... and redo works
        with self.key_down(Keys.CONTROL):
            self.human_key_press('y')
        with self.key_down(Keys.CONTROL):
            self.human_key_press('y')
        self.wait_for_usercode_editor_content(expected_code_after_typing)

        # and typing normally again is fine
        self.human_key_press('abcabc')
        self.wait_for(
            lambda: 'abcabc' in self.get_usercode(),
            lambda: 'could not find abcabc in {}'.format(self.get_usercode()),
        )



    @snapshot_on_error
    def test_code_editor_shows_errors(self):
        # * Harold makes mistakes when writing Python and wants Dirigible to
        #   tell him about them so he can fix them

        error_locator = 'css=div.ace_gutter-cell.ace_error'

        def assert_error(line, message):
            self.wait_for_element_to_appear(error_locator)
            error = self.get_element(error_locator)
            self.assertEquals(error.text, str(line))
            self.assertEquals(error.get_attribute('title'), message)


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
        returned_dict = self.browser.execute_script(dedent(
            """
            var selection = window.editor.getSelectionRange();
            return (
                selection.start.column + ", " + selection.start.row + ", " +
                selection.end.column + ", " + selection.end.row
            );
            """
        ))
        return eval(returned_dict)


    def assert_editor_line_visible(self, line):
        first_visible_row = self.browser.execute_script(
            "return window.editor.getFirstVisibleRow()"
        )
        last_visible_row = self.browser.execute_script(
            "return window.editor.getLastVisibleRow()"
        )
        self.assertLess(int(first_visible_row), line)
        self.assertGreater(int(last_visible_row), line)


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
        self.get_element('id=id_usercode').click()
        with self.key_down(Keys.CONTROL):
            self.human_key_press('f')
        alert = self.browser.switch_to_alert()
        alert.send_keys(123)
        alert.accept()

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
        self.get_element('id=id_usercode').click()
        with self.key_down(Keys.CONTROL):
            self.human_key_press('l')
        alert = self.browser.switch_to_alert()
        alert.send_keys(100)
        alert.accept()

        # The editor jumps to line 100
        self.assertEquals(self.get_editor_selected_range(), (0, 99, 0, 99))

        # The line is, of course, visible.
        self.assert_editor_line_visible(100)
