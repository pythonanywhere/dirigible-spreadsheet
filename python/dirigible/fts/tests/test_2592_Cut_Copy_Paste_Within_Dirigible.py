# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

from textwrap import dedent

from functionaltest import FunctionalTest, Url
import key_codes

class Test_2592_Cut_Copy_Paste_within_Dirigible(FunctionalTest):

    def wait_for_only_active_cell_selected(self):
        def is_only_active_cell_selected():
            return self.selenium.get_eval("""
                (function() {
                    var selectedCells = window.$('.selected');
                    if (selectedCells.length !== 1) {
                        return false;
                    }

                    return selectedCells[0] === window.$('.active')[0];
                })()
            """) == 'true'

        self.wait_for(
            is_only_active_cell_selected,
            lambda: "Only active cell to be selected"
        )


    def test_block_selection(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # He tries to select a range by dragging from B2 to C5
        self.mouse_drag((2, 3), (3, 6))
        self.assert_current_selection((2, 3), (3, 6))

        # he clicks outside the range and sees his selection disappear
        self.click_on_cell(7, 7)
        self.wait_for_only_active_cell_selected()

        # He then uses shift + arrow keys

        # selenium needs a little jquery-kick to get shift-key-down working
        self.selenium.get_eval("window.$('div.grid-canvas').trigger({type:'keydown', which: 16});")

        self.human_key_press(key_codes.LEFT)
        self.assert_current_selection((6, 7), (7, 7))
        self.human_key_press(key_codes.LEFT)
        self.assert_current_selection((5, 7), (7, 7))
        self.human_key_press(key_codes.LEFT)
        self.assert_current_selection((4, 7), (7, 7))
        self.human_key_press(key_codes.UP)
        self.assert_current_selection((4, 6), (7, 7))
        self.human_key_press(key_codes.UP)
        self.assert_current_selection((4, 5), (7, 7))
        self.human_key_press(key_codes.UP)
        self.assert_current_selection((4, 4), (7, 7))
        self.selenium.get_eval("window.$('div.grid-canvas').trigger({type:'keyup', which: 16});")

        # he clicks *inside* the range and sees his selection disappear
        self.click_on_cell(5, 5)
        self.wait_for_only_active_cell_selected()

        # * He finally settles on shift + mouse click as his favourite
        #   method for selecting a range
        self.click_on_cell(2, 3)
        with self.key_down(key_codes.SHIFT):
            self.click_on_cell(8, 7)
        self.assert_current_selection((2, 3), (8, 7))

        # he checks you cannot select the header areas
        self.click_on_cell(1, 1)
        self.selenium.get_eval("window.$('div.grid-canvas').trigger({type:'keydown', which: 16});")
        self.human_key_press(key_codes.LEFT)
        self.assert_current_selection((1, 1), (1, 1))
        self.human_key_press(key_codes.UP)
        self.assert_current_selection((1, 1), (1, 1))


    def assert_copy_and_paste(
        self, operation, source_sheet,
        dest_sheet=None, dest_location=None, to_set='formula'
    ):
        if dest_sheet is None:
            dest_sheet = source_sheet

        # he populates some cells using usercode (because the test runs faster)
        orig_usercode = self.get_usercode()
        self.prepend_usercode(dedent('''
            for row in range(3, 6):
                for col in 'BC':
                    worksheet[col, row].%s = '%%s%%d' %% (col, row)
        ''' % (to_set,)
        ))
        self.wait_for_cell_value(2, 3, 'B3')

        if to_set == 'formula':
            self.enter_usercode(orig_usercode)
            self.wait_for_spinner_to_stop()

        # he copies (or cuts) a region from one place
        operation((2, 3), (3, 5))

        # If he's cutting, it disappears
        if operation == self.cut_range:
            self.wait_for_cell_value(2, 3, '')
            self.wait_for_cell_value(3, 3, '')
            self.wait_for_cell_value(2, 4, '')
            self.wait_for_cell_value(3, 4, '')
            self.wait_for_cell_value(2, 5, '')
            self.wait_for_cell_value(3, 5, '')

        # ...and pastes it elsewhere
        if dest_sheet != source_sheet:
            self.go_to_url( Url.sheet_page(self.get_my_username(), dest_sheet) )
            self.wait_for_grid_to_appear()

        self.paste_range(dest_location)

        # the destination is populated
        c, r = dest_location
        self.wait_for_cell_value(  c,   r, 'B3')
        self.wait_for_cell_value(1+c,   r, 'C3')
        self.wait_for_cell_value(  c, 1+r, 'B4')
        self.wait_for_cell_value(1+c, 1+r, 'C4')
        self.wait_for_cell_value(  c, 2+r, 'B5')
        self.wait_for_cell_value(1+c, 2+r, 'C5')


    def test_copy_and_paste_southeast(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # he does a copy and paste, and sees the destination cells update
        self.assert_copy_and_paste(self.copy_range, sheet_id, dest_location=(3, 4))

        # the non-overlapped source cells are unchanged
        self.wait_for_cell_value(2, 3, 'B3')
        self.wait_for_cell_value(2, 4, 'B4')
        self.wait_for_cell_value(2, 5, 'B5')
        self.wait_for_cell_value(3, 3, 'C3')


    def test_copy_and_paste_northwest(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        self.assert_copy_and_paste(self.copy_range, sheet_id, dest_location=(1, 2))

        # the non-overlapped source cells are unchanged
        self.wait_for_cell_value(2, 5, 'B5')
        self.wait_for_cell_value(3, 3, 'C3')
        self.wait_for_cell_value(3, 4, 'C4')
        self.wait_for_cell_value(3, 5, 'C5')


    def test_copy_and_paste_to_new_sheet(self):
        # * Harold logs in to Dirigible and creates a new sheet
        dest_sheet = self.login_and_create_new_sheet()
        source_sheet = self.create_new_sheet()

        self.assert_copy_and_paste(
            self.copy_range, source_sheet, dest_sheet, dest_location=(3, 4))

        # the cells in the original sheet are all still there
        self.go_to_url( Url.sheet_page(self.get_my_username(), source_sheet) )
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(2, 3, 'B3')
        self.wait_for_cell_value(2, 4, 'B4')
        self.wait_for_cell_value(2, 5, 'B5')
        self.wait_for_cell_value(3, 3, 'C3')
        self.wait_for_cell_value(3, 4, 'C4')
        self.wait_for_cell_value(3, 5, 'C5')


    def test_cut_and_paste_southeast(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        self.assert_copy_and_paste(self.cut_range, sheet_id, dest_location=(3, 4))

        # the source cells that weren't pasted over are cleared
        self.wait_for_cell_value(2, 3, '')
        self.wait_for_cell_value(3, 3, '')
        self.wait_for_cell_value(2, 4, '')
        self.wait_for_cell_value(2, 5, '')


    def test_cut_and_paste_northwest(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        self.assert_copy_and_paste(self.cut_range, sheet_id, dest_location=(1, 2))

        # the source cells that weren't pasted over are cleared
        self.wait_for_cell_value(2, 5, '')
        self.wait_for_cell_value(3, 3, '')
        self.wait_for_cell_value(3, 4, '')
        self.wait_for_cell_value(3, 5, '')


    def test_cut_and_paste_to_new_sheet(self):
        # * Harold logs in to Dirigible and creates two new sheets
        dest_sheet = self.login_and_create_new_sheet()
        source_sheet = self.create_new_sheet()

        # He cuts stuff from one to the other
        self.assert_copy_and_paste(
            self.cut_range, source_sheet, dest_sheet, dest_location=(3, 4))


    def test_multiple_pastes_after_copy(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # He copies some stuff towards the southeast
        self.assert_copy_and_paste(self.copy_range, sheet_id, dest_location=(3, 4))

        # the non-overlapped source cells are unchanged
        self.wait_for_cell_value(2, 3, 'B3')
        self.wait_for_cell_value(2, 4, 'B4')
        self.wait_for_cell_value(2, 5, 'B5')
        self.wait_for_cell_value(3, 3, 'C3')

        # he then tries pasting again, even further south east.
        c, r = 10, 20
        self.paste_range((c, r))

        # the destination is populated
        self.wait_for_cell_value(  c,   r, 'B3')
        self.wait_for_cell_value(1+c,   r, 'C3')
        self.wait_for_cell_value(  c, 1+r, 'B4')
        self.wait_for_cell_value(1+c, 1+r, 'C4')
        self.wait_for_cell_value(  c, 2+r, 'B5')
        self.wait_for_cell_value(1+c, 2+r, 'C5')

        # the source and original paste are unchanged
        self.wait_for_cell_value(2, 3, 'B3')
        self.wait_for_cell_value(3, 4, 'B3')

        # he sets a cell formula
        self.enter_cell_text(1, 1, "hope this doesn't kill the clipboard!")
        self.wait_for_cell_value(1, 1, "hope this doesn't kill the clipboard!")

        # he tries to paste again slightly southeast
        c, r = 11, 21
        self.paste_range((c, r))

        # and is pleased to see the destination populated
        self.wait_for_cell_value(  c,   r, 'B3')
        self.wait_for_cell_value(1+c,   r, 'C3')
        self.wait_for_cell_value(  c, 1+r, 'B4')
        self.wait_for_cell_value(1+c, 1+r, 'C4')
        self.wait_for_cell_value(  c, 2+r, 'B5')
        self.wait_for_cell_value(1+c, 2+r, 'C5')

        # he double checks the source and earlier pastes are unchanged
        self.wait_for_cell_value(2, 3, 'B3')
        self.wait_for_cell_value(3, 4, 'B3')
        self.wait_for_cell_value(10, 20, 'B3')


    def test_multiple_pastes_after_cut(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        #  He cuts & pastes some stuff towards the southeast
        self.assert_copy_and_paste(self.cut_range, sheet_id, dest_location=(3, 4))

        # he hits paste again, further down
        c, r = 10, 20
        self.paste_range((c, r))

        # the destination is populated
        self.wait_for_cell_value(  c,   r, 'B3')
        self.wait_for_cell_value(1+c,   r, 'C3')
        self.wait_for_cell_value(  c, 1+r, 'B4')
        self.wait_for_cell_value(1+c, 1+r, 'C4')
        self.wait_for_cell_value(  c, 2+r, 'B5')
        self.wait_for_cell_value(1+c, 2+r, 'C5')

        # he now sets a cell formula
        self.enter_cell_text(1, 1, "hope this doesn't kill the clipboard!")
        self.wait_for_cell_value(1, 1, "hope this doesn't kill the clipboard!")

        # he tries to paste again slightly southeast
        c, r = 11, 21
        self.paste_range((c, r))

        # and is pleased to see the destination populated
        self.wait_for_cell_value(  c,   r, 'B3')
        self.wait_for_cell_value(1+c,   r, 'C3')
        self.wait_for_cell_value(  c, 1+r, 'B4')
        self.wait_for_cell_value(1+c, 1+r, 'C4')
        self.wait_for_cell_value(  c, 2+r, 'B5')
        self.wait_for_cell_value(1+c, 2+r, 'C5')

        # he double checks the original source is still empty
        self.wait_for_cell_value(2, 3, '')

        #and earlier pastes are unchanged
        self.wait_for_cell_value(3, 4, 'B3')
        self.wait_for_cell_value(10, 20, 'B3')


    def test_values_wo_formulae_are_promoted(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # he sets up a range with just values, no formulae, and checks they get
        # copied
        self.assert_copy_and_paste(self.copy_range, sheet_id,
            dest_location=(3, 4), to_set='value')


    def test_target_range_is_cleared_before_paste(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some values into the grid
        #   making sure that there are some gaps
        for row in range(1, 6, 2):
            self.enter_cell_text(1, row, 'filled')
        self.copy_range((1, 1), (1, 6))

        # * He copies a section of the values over another section
        #   and notes that the gaps in the source range are replicated in the target
        self.paste_range((1, 2))
        self.wait_for_cell_value(1, 3, '')


    def test_mouse_drags_dont_lose_current_cell_edits(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        self.click_on_cell(1, 1)
        self.human_key_press(key_codes.NUMBER_1)
        self.human_key_press(key_codes.NUMBER_2)

        self.mouse_drag((2, 3), (3, 6))
