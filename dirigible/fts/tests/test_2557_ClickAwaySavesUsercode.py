# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest


class Test_2557_ClickAwaySavesUsercode(FunctionalTest):

    def test_blur_on_edit_textarea_saves_usercode(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He enters some usercode that sets A1 to 4
        self.selenium.get_eval('window.editor.focus()')
        self.enter_usercode('worksheet[1, 1].value = 4')

        # * He does something to cause a blur event on the editarea textbox
        ## We use fire_event because Selenium does not fire the full event stack
        ## for clicks. If this changes in future Selenium versions, it would be nice
        ## to expand this test to check behaviour for clicking on cells, links and
        ## edit sheet name
        self.selenium.get_eval("window.editor.blur()")

        # * ... and notes that A1 contains 4
        self.wait_for_cell_value(1, 1, '4')
