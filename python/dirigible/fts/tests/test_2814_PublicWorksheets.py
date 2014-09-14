# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#
from __future__ import with_statement

from os import path
import re
import time
from urllib2 import HTTPError
from urlparse import urljoin

from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT, SERVER_IP
import key_codes

class Test_2814_PublicWorksheets(FunctionalTest):
    user_count = 3
    email_address = None


    def tearDown(self):
        FunctionalTest.tearDown(self)
        if self.email_address:
            self.clear_email_for_address(self.email_address)


    def waitForButtonToIndicateSheetIsPublic(self, public):
        if public:
            expected_text = 'Sheet is public'
        else:
            expected_text = 'Sheet is private'

        def get_button_title():
            return self.selenium.get_attribute('css=#id_security_button@title')
        self.wait_for(
            lambda : expected_text in get_button_title(),
            lambda : "%r to be in %r" % (expected_text, get_button_title())
        )

        def get_button_alt_text():
            return self.selenium.get_attribute('css=#id_security_button@alt')
        self.wait_for(
            lambda : expected_text in get_button_alt_text(),
            lambda : "%r to be in %r" % (expected_text, get_button_alt_text())
        )


    def test_public_worksheets_visible_readonly_and_copiable_for_others(self):
        # * Harold logs in and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()

        # * He gives the sheet a catchy name
        self.set_sheet_name('spaceshuttle')

        # * He enters some formulae n stuff
        self.enter_cell_text(2, 3, '23')
        self.enter_cell_text(2, 4, '=my_add_function(B3)')
        self.prepend_usercode('my_add_function = lambda x : x + 2')
        self.wait_for_cell_value(2, 4, '25')

        # * He notes that the tooltip for the security icon indicates that the
        # sheet is private
        self.waitForButtonToIndicateSheetIsPublic(False)

        # * He clicks on the security icon
        self.selenium.click('id=id_security_button')

        # He sees a tickbox, currently unticked, saying make worksheet public
        self.wait_for_element_visibility(
                'id=id_security_form', True)
        self.wait_for_element_visibility(
                'id=id_security_form_public_sheet_checkbox', True)

        self.assertEquals(
            self.selenium.get_value('id=id_security_form_public_sheet_checkbox'),
            'off'
        )
        # He ticks it and dismisses the dialog
        self.selenium.click('id=id_security_form_public_sheet_checkbox')
        self.selenium.click('id=id_security_form_ok_button')

        # * He notes that the tooltip for the security icon indicates that the
        # sheet is public
        self.waitForButtonToIndicateSheetIsPublic(True)

        # He notes down the URL and emails it to his colleague Harriet
        harolds_url = self.browser.current_url

        # He logs out
        self.logout()

        # * Later on, Harriet logs into teh Dirigible and heads on over to
        #   Harold's spreadsheet
        self.login(self.get_my_usernames()[1])
        self.go_to_url(harolds_url)

        # She sees the values n stuff
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(2, 4, '25')

        # * She notices that all toolbar icons are missing,
        # apart from download-as-csv
        map(
            lambda e: self.wait_for_element_presence(e, False),
            [
                'id=id_import_button',
                'id=id_cut_button',
                'id=id_copy_button',
                'id=id_paste_button',
                'id=id_security_button',
            ]
        )
        self.wait_for_element_visibility('id=id_export_button', True)

        # * She tries to edit some formulae, but can't
        self.selenium.double_click(
                self.get_cell_locator(1, 1)
        )
        self.selenium.focus(
                self.get_cell_locator(1, 1)
        )
        time.sleep(1)
        self.wait_for_element_presence(
                self.get_active_cell_editor_locator(),
                False
        )

        # * she tries to edit the cell again, using the formula bar, but cannot
        self.assertEquals(
            self.selenium.get_attribute(self.get_formula_bar_locator() + '@readonly'),
            'true'
        )

        # * She tries to edit some usercode, but can't
        original_code = self.get_usercode()
        self.selenium.get_eval('window.editor.focus()')
        self.human_key_press(key_codes.LETTER_A)
        time.sleep(1)
        self.wait_for_usercode_editor_content(original_code)

        # * She tries to edit the sheet name, but can't

        # * mouses over the sheet name and notes that the appearance
        #   does not change to indicate that it's editable
        self.selenium.mouse_over('id=id_sheet_name')
        time.sleep(1)
        self.wait_for(
            lambda: self.get_css_property('#id_sheet_name', 'background-color') == 'transparent',
            lambda: 'ensure sheet name background stays normal')

        # * He clicks on the sheet name, the sheetname edit textarea does
        #   not appear,
        self.selenium.click('id=id_sheet_name')
        time.sleep(1)
        self.wait_for(
            lambda: not self.selenium.is_element_present('id=edit-id_sheet_name'),
            lambda: 'ensure editable sheetname does not appear')

        def download_as_csv():
            self.selenium.click('id=id_export_button')
            self.wait_for_element_visibility('id=id_export_dialog', True)
            download_url = self.selenium.get_attribute('id=id_export_csv_excel_version@href')
            download_url = urljoin(self.browser.current_url, download_url)

            stream = self.get_url_with_session_cookie(download_url)
            self.assertEquals(stream.info().gettype(), "text/csv")
            self.assertEquals(
                    stream.info()['Content-Disposition'],
                    'attachment; filename=spaceshuttle.csv'
            )

            expected_file_name = path.join(
                    path.dirname(__file__),
                    "test_data", "public_sheet_csv_file.csv"
            )
            with open(expected_file_name) as expected_file:
                self.assertEquals(
                    stream.read().replace("\r\n", "\n"),
                    expected_file.read().replace("\r\n", "\n")
                )

        # * She confirms that she can download a csv of the sheet
        download_as_csv()

        # * She uses some l33t haxx0ring skillz to try and send a
        #   setcellformula Ajax call directly
        # It doesn't work.
        with self.assertRaises(HTTPError):
            response = self.get_url_with_session_cookie(
                    urljoin(harolds_url, '/set_cell_formula/'),
                    data={'column':3, 'row': 4, 'formula': '=jeffk'}
            )

        # * "Aha!" she says, as she notices a link allowing her to copy the sheet,
        self.wait_for_element_visibility('id_copy_sheet_link', True)
        # which she then clicks
        self.selenium.click('id=id_copy_sheet_link')

        # She is taken to a sheet of her own
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_grid_to_appear()

        # It looks a lot like Harold's but has a different url
        harriets_url = self.browser.current_url
        self.assertFalse(harriets_url == harolds_url)
        self.wait_for_cell_value(2, 4, '25')

        # And she is able to change cell formulae
        self.enter_cell_text(2, 3, '123')
        self.wait_for_cell_value(2, 4, '125')

        # And she is able to change usercode
        self.append_usercode('worksheet[2, 4].value += 100')
        self.wait_for_cell_value(2, 4, '225')

        # And she is well pleased. So much so that she emails two
        # friends about these two sheets (and they tell two
        # friends, and they tell two friends, and so on, and so
        # on.  $$$$)
        self.logout()

        # * Helga is a Dirigible user, but she isn't logged in.
        #   She goes to Harold's page, and sees that it is good.
        self.go_to_url(harolds_url)
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(2, 4, '25')

        # She clicks on the big copy button, and is taken to the
        # login form
        self.selenium.click('id=id_copy_sheet_link')
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_element_visibility('id_login_form_wrap', True)

        # She logs in, and is taken straight to her new copy of
        # Harold's sheet
        self.login(
                self.get_my_usernames()[2],
                already_on_login_page=True
        )
        self.wait_for_grid_to_appear()

        helgas_url = self.browser.current_url
        self.assertFalse(helgas_url == harolds_url)
        self.assertFalse(helgas_url == harriets_url)
        self.wait_for_cell_value(2, 4, '25')

        # Helga makes some edits, which she considers superior to
        # Harriet's
        self.enter_cell_text(2, 3, '1000')
        self.append_usercode('worksheet[2, 4].value += 1000')
        self.wait_for_cell_value(2, 4, '2002')

        # Helga now decides to go and see Harriet's sheet, to
        # laugh at the inferiority of Harriet's fork
        # Her access is denied.
        self.assert_HTTP_error(harriets_url, 403)

        # * Harriet's other friend, Hugh, is not a Dirigible user.... yet.
        # He goes to Harold's sheet and sees that it is good
        self.logout()
        self.go_to_url(harolds_url)
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(2, 4, '25')

        # So good that he clicks the copy button too, despite never
        # having heard of this Dirigible thingy
        self.selenium.click('id=id_copy_sheet_link')
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)

        # He is taken to the login form,
        self.wait_for_element_visibility('id_login_form_wrap', True)

        # on which he spots a nice friendly link inviting him to register.
        # It says 'free' and everyfink.
        self.wait_for_element_to_appear('id=id_login_signup_link')
        self.wait_for_element_to_appear('id=id_login_signup_blurb')
        self.assertTrue("free" in self.selenium.get_text('id=id_login_signup_blurb'))

        # Hugh goes through the whole registration rigmarole,
        self.selenium.click('id=id_login_signup_link')
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        username = self.get_my_username() + "_x"
        self.email_address = 'harold.testuser-%s@resolversystems.com' % (username,)
        password = "p4ssw0rd"
        self.selenium.type('id=id_username', username)
        self.selenium.type('id=id_email', self.email_address)
        self.selenium.type('id=id_password1', password)
        self.selenium.type('id=id_password2', password)
        self.click_link('id_signup_button')

        email_from, email_to, subject, message = self.pop_email_for_client(self.email_address)
        self.assertEquals(subject, 'Dirigible Beta Sign-up')
        confirm_url_re = re.compile(
            r'<(http://projectdirigible\.com/signup/activate/[^>]+)>'
        )
        match = confirm_url_re.search(message)
        self.assertTrue(match)
        confirmation_url = match.group(1).replace('projectdirigible.com', SERVER_IP)

        # * Hugh then logs in
        self.go_to_url(confirmation_url)
        self.login(username, password, already_on_login_page=True)

        # and has his socks knocked off by the presence of the copy of Harold's
        # sheet in his dashboard
        self.selenium.click('link=spaceshuttle')

        # and it has the copied content
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(2, 4, '25')

        # Harold logs in and sees that his original sheet is unharmed by all of
        # the other users editing theirs
        self.login(self.get_my_usernames()[0])
        self.go_to_url(harolds_url)
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(2, 4, '25')


    def test_admin_can_copy_non_public_sheets(self):
        # * Harold logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()
        self.enter_cell_text(1, 1, '=6 + 11')

        # * He is having some trouble working with a complicated task
        #   so he asks an admin for help. Giving him the sheet url
        sheet_url = '/user/%s/sheet/%s' % (self.get_my_username(), sheet_id)
        self.logout()

        # * The admin logs in and visits the sheet
        self.login('admin', '<KI*7ujm')
        self.go_to_url(sheet_url)

        # * He copies the sheet to his own account so he can edit it without
        #   changing Harold's sheet
        self.selenium.click('id=id_copy_sheet_link')
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.wait_for_grid_to_appear()
        self.wait_for_cell_value(1, 1, '17')


    def test_link_to_documentation_in_dialog(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He goes to the security dialog.
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)

        # * He is puzzled by the public sheet option, so he clicks on its help link
        # * The link goes into a new window
        ## Selenium gets Very Unhappy with target=_blank, so we just check that it's there and
        ## then remove it so as not to frighten the poor thing.
        self.assertEquals(
            self.selenium.get_attribute('id=id_security_form_public_sheet_help@target'),
            "_blank"
        )
        self.selenium.get_eval("window.$('#id_security_form_public_sheet_help').removeAttr('target')")
        self.selenium.click("id=id_security_form_public_sheet_help")
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)

        # * and is taken to a documentation page that explains it all
        title = self.selenium.get_title().lower()
        self.assertTrue('public' in title)
        self.assertTrue('sheet' in title)

