# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from __future__ import with_statement

try:
    import json
except ImportError:
    import simplejson as json
from urllib import urlencode
from urllib2 import urlopen, HTTPError
from urlparse import urljoin, urlparse

# these can't be imported on non-windows machines, but we need to import test
# modules on our *nix integration master without running them, to run the build
try:
    from win32clipboard import OpenClipboard, GetClipboardData, CloseClipboard
    import win32con
except:
    pass

import key_codes
from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT, Url


class Test_2565_JSONAPIAuth(FunctionalTest):

    def test_json_api_auth(self):
        # Harold wants to make sure that people only have JSON access to his sheets
        # when he has explicitly granted it.

        # * He logs in to Dirigible and creates a new sheet
        sheet_id = self.login_and_create_new_sheet()
        base_json_url = urljoin(self.browser.current_url, 'v0.1/json/')

        # * He enters some values and formulae
        self.enter_cell_text(1, 1, '5')

        # * He tries to use an API call to get the sheet as JSON, but gets a 403 error.
        with self.assertRaises(HTTPError) as mngr:
            urlopen(base_json_url)
        self.assertEquals(mngr.exception.code, 403)

        # * Looking around at the sheet page, he notices a "Security" button.
        self.wait_for_element_to_appear('id=id_security_button')

        # * He sees that the mouseover text on the button indicates that the JSON API is not enabled
        self.assertTrue(
            'JSON API disabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API disabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )

        # * He clicks the button.
        self.selenium.click('id=id_security_button')

        # * A dialog appears; there is an unchecked toggle saying "Allow JSON API access"
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.wait_for_element_visibility('id=id_security_form_json_enabled_checkbox', True)
        self.wait_for_element_visibility('id=id_security_form_json_api_key', True)
        self.wait_for_element_visibility('id=id_security_form_json_api_url', True)

        self.assertFalse(self.is_element_enabled('id_security_form_json_api_key'))
        self.assertFalse(self.is_element_enabled('id_security_form_json_api_url'))

        self.assertEquals(
            self.get_text('css=label[for="id_security_form_json_enabled_checkbox"]'),
            'Allow JSON API access'
        )
        self.assertEquals(self.selenium.get_value('id=id_security_form_json_enabled_checkbox'), 'off')

        # * ... and OK and Cancel buttons
        self.wait_for_element_visibility('id=id_security_form_ok_button', True)
        self.wait_for_element_visibility('id=id_security_form_cancel_button', True)

        # * He checks it.  He notices a textbox giving him an "API key",
        self.selenium.click('id=id_security_form_json_enabled_checkbox')
        self.assertTrue(self.is_element_enabled('id_security_form_json_api_key'))
        api_key = self.selenium.get_value('id=id_security_form_json_api_key')
        api_url = self.selenium.get_value('id=id_security_form_json_api_url')

        # * He also notices that when he clicks on the URL text field, the entire field is selected
        ## The focus call is to appease Chrome
        self.selenium.focus('id=id_security_form_json_api_url')
        self.selenium.click('id=id_security_form_json_api_url')

        # our 'caret' plugin appears to have a problem getting the selection
        # range for fields that are not editable, such as the json api url.
        # Consequently, we have to check the selection by copying this
        # text, and checking the clipboard content.
        with self.key_down(key_codes.CTRL):
            self.human_key_press(key_codes.LETTER_C)

        def get_clipboard_text():
            OpenClipboard()
            text = GetClipboardData(win32con.CF_TEXT)
            CloseClipboard()
            return text

        self.wait_for(
            lambda: get_clipboard_text() == api_url,
            lambda: 'bad clipboard text, was: %s' % (get_clipboard_text(),)
        )

        # * nothing appears outside the JSON API dialog box yet though.
        self.assertTrue(
            'JSON API disabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API disabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )

        # * He ignores all of the key stuff, presses Cancel
        self.selenium.click('id=id_security_form_cancel_button')

        # * He notices that the form disappears and that the icon still indicates that the JSON API is disabled
        self.wait_for_element_visibility('id=id_security_form', False)
        self.assertTrue(
            'JSON API disabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API disabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )

        # but he just tries accessing the JSON URL without a key again
        # * He gets 403 again.
        with self.assertRaises(HTTPError) as mngr:
            urlopen(base_json_url)
        self.assertEquals(mngr.exception.code, 403)

        # * and he also gets 403 when he uses the API Key that was displayed
        with self.assertRaises(HTTPError) as mngr:
            urlopen(base_json_url, urlencode({'api_key': api_key}))
        self.assertEquals(mngr.exception.code, 403)

        # * He half-realises what the problem is, opens the dialog again, checks the box, and presses OK
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.assertEquals(self.selenium.get_value('id=id_security_form_json_enabled_checkbox'), 'off')
        self.selenium.click('id=id_security_form_json_enabled_checkbox')
        self.assertTrue(self.is_element_enabled('id_security_form_json_api_key'))
        self.assertTrue(self.is_element_enabled('id_security_form_json_api_url'))
        api_url = self.selenium.get_value('css=#id_security_form_json_api_url')
        self.selenium.click('id=id_security_form_ok_button')
        self.wait_for_element_visibility('id=id_security_form', False)

        #* He now sees the toolbar indicates that the JSON API is enabled for this sheet
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )

        # * Not trusting the memory of his browser, he opens the dialog again
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.assertEquals(self.selenium.get_value('id=id_security_form_json_enabled_checkbox'), 'on')

        # * and immediately presses Cancel
        self.selenium.click('id=id_security_form_cancel_button')

        # * He is surprised and delighted to see that his sheet is still JSON-enabled
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )

        expected_url = "%s%s?api_key=%s" % (
            self.selenium.browserURL[:-1],
            urlparse(Url.api_url(self.get_my_username(), sheet_id)).path,
            api_key
        )
        self.assertEquals(api_url, expected_url)

        # .. despite this helpful link, he tries again with the wrong API key
        with self.assertRaises(HTTPError) as mngr:
            urlopen(base_json_url, urlencode({'api_key': 'abcd1234-123dfe'}))
        # * He gets a 403
        self.assertEquals(mngr.exception.code, 403)


        # * Frustrated, he tries again with the right API key.
        response = urlopen(base_json_url, urlencode({'api_key': api_key}))

        # * He gets the data he expected.
        json_data = json.load(response)
        self.assertEquals(json_data['1']['1'], 5)

        # * He changes the API key in the JSON API dialog.
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        old_api_url = self.selenium.get_value('css=#id_security_form_json_api_url')
        self.selenium.type('id=id_security_form_json_api_key', 'some_new_api_ke')
        self.selenium.focus('id=id_security_form_json_api_key')

        # He sees that the api url is updated with every keystroke
        self.human_key_press(key_codes.END) # Move IE insert point to the end
        self.human_key_press(key_codes.LETTER_Y)

        self.assertEquals(
            self.selenium.get_value('css=#id_security_form_json_api_url'),
            old_api_url.replace(api_key, 'some_new_api_key')
        )
        self.selenium.click('id=id_security_form_ok_button')
        self.wait_for_element_visibility('id=id_security_form', False)

        # * He tries again, using the old key
        with self.assertRaises(HTTPError) as mngr:
            urlopen(base_json_url, urlencode({'api_key': api_key}))
        # * He gets a 403
        self.assertEquals(mngr.exception.code, 403)

        # * He tries using the right key.
        response = urlopen(base_json_url, urlencode({'api_key': 'some_new_api_key'}))

        # * It works.
        json_data = json.load(response)
        self.assertEquals(json_data['1']['1'], 5)

        # * He refreshes the sheet page
        self.refresh_sheet_page()

        # * and notes that his setting has been remembered by the server
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.assertEquals(self.selenium.get_value('id=id_security_form_json_enabled_checkbox'), 'on')

        # * He makes the sheet private again.
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.selenium.click('id=id_security_form_json_enabled_checkbox')
        self.selenium.click('id=id_security_form_ok_button')
        self.wait_for_element_visibility('id=id_security_form', False)

        # * He tries with the key that worked last time.
        with self.assertRaises(HTTPError) as mngr:
            urlopen(base_json_url, urlencode({'api_key': 'some_new_api_key'}))
        # * He gets a 403
        self.assertEquals(mngr.exception.code, 403)


    def test_link_to_documentation_in_dialog(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He goes to the security dialog.
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)

        # * He is puzzled by the JSON API option, so he clicks on its help link
        # * The link goes into a new window
        ## Selenium gets Very Unhappy with target=_blank, so we just check that it's there and
        ## then remove it so as not to frighten the poor thing.
        self.assertEquals(
            self.selenium.get_attribute('id=id_security_form_json_help@target'),
            "_blank"
        )
        self.selenium.get_eval("window.$('#id_security_form_json_help').removeAttr('target')")
        self.selenium.click("id=id_security_form_json_help")
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)

        # containing a documentation page that explains it all
        title = self.selenium.get_title()
        self.assertTrue(title.startswith('The JSON API'))
        self.assertTrue(title.endswith('documentation'))


    def test_run_worksheet_with_json_disabled_sheets(self):
        # * Harold logs in to Dirigible and creates a new sheet, with some stuff in it
        self.login_and_create_new_sheet()
        rws_sheet_url = self.browser.current_url
        self.enter_cell_text(1, 1, '5')

        # * He creates another new sheet
        self.create_new_sheet()
        base_json_url = urljoin(self.browser.current_url, 'v0.1/json/')

        # * and enables JSON API access
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.selenium.click('id=id_security_form_json_enabled_checkbox')
        self.selenium.type('id=id_security_form_json_api_key', self.get_my_username())
        self.selenium.click('id=id_security_form_ok_button')
        self.wait_for_element_visibility('id=id_security_form', False)

        # * He enters a formula that uses run_worksheet on the first sheet
        self.enter_cell_text(1, 1, "=run_worksheet('%s')[1, 1].value" % (rws_sheet_url,))
        self.wait_for_cell_value(1, 1, '5')

        # * and tries to access it via the JSON API
        try:
            response = urlopen(base_json_url, urlencode({'api_key': self.get_my_username()}))
        except HTTPError, err:
            self.fail(err.read())

        # * It works.
        json_data = json.load(response)
        self.assertEquals(json_data['1']['1'], 5)


    def test_json_api_auth_reports_server_error(self):
        # * Harold logs in to Dirigible and creates a new sheet, with some stuff in it
        self.login_and_create_new_sheet()

        # * and enables JSON API access
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)
        self.selenium.click('id=id_security_form_json_enabled_checkbox')
        self.selenium.type('id=id_security_form_json_api_key', self.get_my_username())

        # Something goes wrong with the Dirigible server
        old_set_security_settings_url = self.selenium.get_eval("window.urls.setSecuritySettings")
        self.selenium.get_eval("window.urls.setSecuritySettings = 'blergh'")

        # Blissfully unaware of this, Harold clicks OK.
        self.selenium.click('id=id_security_form_ok_button')

        # The dialog remains, and an error div appears to tell him that something is wrong.
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', True)

        # He waits for a moment, and the server magically fixes itself.
        self.selenium.get_eval("window.urls.setSecuritySettings = '%s'" % (old_set_security_settings_url,))

        # He tries again, and the dialog disappears.
        self.selenium.click('id=id_security_form_ok_button')
        self.wait_for_element_visibility('id=id_security_form', False)

        # The sheet page confirms that his changes are there.
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )

        # He pops up the dialog and is pleased to see that there is no error message there.
        self.selenium.click('id=id_security_button')
        self.wait_for_element_visibility('id=id_security_form', True)
        self.wait_for_element_visibility('id=id_security_form_save_error', False)

        # He refreshes the page and confirms from the toolbar buttons that his changes really were saved.
        self.refresh_sheet_page()
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@title')
        )
        self.assertTrue(
            'JSON API enabled' in
            self.selenium.get_attribute('css=#id_security_button@alt')
        )
