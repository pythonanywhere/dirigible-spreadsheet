# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest
from textwrap import dedent

import key_codes


class Test_2550_EdittableSheetName(FunctionalTest):

    def test_sheet_name_edittable(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notes that the sheet has a name of the form 'Sheet #xx'
        #   where xx is the sheet id
        sheet_id = self.browser.current_url.split(r'/')[-2]
        self.assertEquals(
            self.get_text('id=id_sheet_name'),
            'Sheet %s' % (sheet_id,))

        # * He mouses over the sheet name and notes that the appearance
        #   changes to indicate that it's editable
        self.selenium.mouse_over('id=id_sheet_name')
        self.wait_for(
            lambda: self.get_css_property('#id_sheet_name', 'background-color') == '#D1D2D4',
            lambda: 'sheet name background to darken')

        # * He moves the mouse away - it changes back
        self.selenium.mouse_out('id=id_sheet_name')
        self.wait_for(
            lambda: self.get_css_property('#id_sheet_name', 'background-color') == 'transparent',
            lambda: 'sheet name background to return to normal')

        # * He clicks on the sheet name, the sheeetname edit textarea appears,
        # and remains when the mouse moves away
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'editable sheetname to appear')
        self.selenium.mouse_out('id=id_sheet_name')
        self.assertTrue(self.selenium.is_element_present('id=edit-id_sheet_name'))

        # * He types a new sheetname 'margarita', hits return.
        self.selenium.type('id=edit-id_sheet_name', 'margarita')
        self.human_key_press(key_codes.ENTER)

        #   The sheetname is modified
        self.wait_for(
            lambda: self.get_text('id=id_sheet_name') == 'margarita',
            lambda: 'sheet name to be updated'
        )
        # and the title to the page becomes "user's sheet_name: Dirigible"
        self.assertEquals(self.selenium.get_title(), "%s's %s: Dirigible" %
            (self.get_my_username(), 'margarita'))

        # * He refreshes the page
        self.refresh_sheet_page()

        #   The new sheetname persists
        self.wait_for(
            lambda: self.get_text('id=id_sheet_name') == 'margarita',
            lambda: 'sheet name to be updated'
        )
        # and the title to the page remains "user's sheet_name: Dirigible"
        self.wait_for(
            lambda: self.selenium.get_title() == "%s's %s: Dirigible" % (self.get_my_username(), 'margarita'),
            lambda: 'page title to update'
        )


    def test_changing_sheet_name_should_not_interrupt_recalc_but_still_succeeds(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters usercode that takes a long time to run
        self.enter_cell_text(1, 1, '')
        self.enter_usercode(dedent('''
            import time
            time.sleep(20)
            worksheet[1, 1].value = 'recalced'
        '''))

        # * While the recalc is running, he changes the sheet name
        self.selenium.click('id=id_sheet_name')
        self.wait_for(
            lambda: self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'editable sheetname to appear')
        self.selenium.type('id=edit-id_sheet_name', 'new sheet name')
        self.human_key_press(key_codes.ENTER)

        # * The recalculation finishes normally and his sheet has a new name
        self.wait_for_cell_value(1, 1, 'recalced', timeout_seconds=21)
        self.assertEquals(self.get_text('id=id_sheet_name'), 'new sheet name')

        # * he checks that the new sheetname sticks after a page refresh
        self.refresh_sheet_page()
        self.assertEquals(self.get_text('id=id_sheet_name'), 'new sheet name')



