# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest, snapshot_on_error, Url


class Test_2531_DifficultStuffInCells(FunctionalTest):

    @snapshot_on_error
    def test_list_in_cell(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters "=[1, 2, 3]" in A1.
        self.enter_cell_text(1, 1, '=[1, 2, 3]')

        # * When he moves away from the cell, "[1, 2, 3]" is there
        self.click_on_cell(2, 1)
        self.wait_for_cell_value(1, 1, '[1, 2, 3]')

        # * He enters a list comprehension in A2.
        self.enter_cell_text(1, 2, '=[x*2 for x in A1]')
        self.click_on_cell(2, 2)
        self.wait_for_cell_value(1, 2, '[2, 4, 6]')


    def test_dictionary_in_cell(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters "={'key'->'value', 'key2'->3}" in A1.
        self.enter_cell_text(1, 1, "={'key'  ->'value', 'key2'->  3}")

        # * When he moves away from the cell, "{'key':'value', 'key2':3}" is there
        self.click_on_cell(2, 1)
        self.wait_for_cell_value(1, 1, repr({'key':'value', 'key2':3}))


    def test_object_in_cell(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters "=object()" in A1.
        self.enter_cell_text(1, 1, '=object()')
        self.click_on_cell(2, 1)

        # * When he moves away from the cell, the obj is visible
        self.wait_for(
            lambda: self.get_cell_text(1, 1).startswith('<object object at 0x'),
            lambda: 'object to appear in cell')

        # * Feeling perverse, he decides to create his own class and shove it into the grid
        self.prepend_usercode(dedent('''
        class Perverse(object):
            t = 'blah'

        p = Perverse()
        '''))
        self.enter_cell_text(3, 1, '=p')
        self.click_on_cell(3, 4)

        # * He sees the string representation of his new object
        self.wait_for(
            lambda: self.get_cell_text(3, 1).startswith('<Perverse object at 0x'),
            lambda: 'user-defined object to appear in cell')


    def assert_input_roundtrips(self, typed):
        # * He enters an html tag in A1
        self.row += 1
        self.enter_cell_text(1, self.row, typed)
        self.wait_for_cell_value(1, self.row, typed)
        self.open_cell_for_editing(1, self.row)
        self.wait_for_cell_editor_content(typed)

        self.enter_cell_text(2, self.row, '="%s"' % (typed, ))
        self.wait_for_cell_value(2, self.row, '%s' % (typed,))
        self.open_cell_for_editing(2, self.row)
        self.wait_for_cell_editor_content('="%s"' % (typed, ))


    def test_html_chars_escaped(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters html tags and chars that look like escaped html tags
        self.row = 1
        self.assert_input_roundtrips('<br />')
        self.assert_input_roundtrips('fish&chips')
        self.assert_input_roundtrips('&lt;')
        self.assert_input_roundtrips('&gt;')
        self.assert_input_roundtrips('&amp;')


    @snapshot_on_error
    def test_numeric_types(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        self.enter_cell_text(1, 1, '999')
        self.wait_for_cell_value(1, 1, '999')
        self.open_cell_for_editing(1, 1)
        self.wait_for_cell_editor_content('999')
        self.append_usercode("worksheet[1, 2].value = type(worksheet[1, 1].value)")
        self.wait_for_cell_value(1, 2, "<type 'int'>")

        self.enter_cell_text(2, 1, '999.0')
        self.wait_for_cell_value(2, 1, '999.0')
        self.open_cell_for_editing(2, 1)
        self.wait_for_cell_editor_content('999.0')
        self.append_usercode("worksheet[2, 2].value = type(worksheet[2, 1].value)")
        self.wait_for_cell_value(2, 2, "<type 'float'>")
