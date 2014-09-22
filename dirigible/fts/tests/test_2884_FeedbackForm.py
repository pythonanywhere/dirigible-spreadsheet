# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest, Url


class Test_2884_FeedbackForm(FunctionalTest):

    def tearDown(self):
        FunctionalTest.tearDown(self)
        self.clear_email_for_address(
            'harold.testuser-admin@projectdirigible.com',
            content_filter=self.get_my_username()
        )


    def test_feedback_dialog_from_non_logged_in_page(self):
        # * Harold is not logged in, and goes to the root Dirigible page.
        self.go_to_url(Url.ROOT)

        # * he clicks the feedback link
        self.selenium.click('link=Feedback')
        self.wait_for_element_visibility('id=id_feedback_dialog', True)

        #  * titled:
        self.assertEquals('Help us improve',
            self.get_text('css=.ui-dialog-title')
        )
        #  * with some friendly text:
        self.assertEquals(
            "It's always a pleasure to hear from you!",
            self.get_text('css=#id_feedback_dialog_blurb_big')
        )
        self.assertEquals(
            "Ask us a question, or tell us what you love or hate about Dirigible:",
            self.get_text('css=#id_feedback_dialog_blurb_small')
        )
        #   * with a big freeform input field
        #     which has the focus
        self.wait_for_element_visibility('id=id_feedback_dialog_text', True)
        self.assertTrue(self.is_element_focused('id=id_feedback_dialog_text'))

        #   * an email field:
        self.wait_for_element_visibility('id=id_feedback_dialog_email_address', True)
        #   The email field has a value indicating what it's for:
        self.assertEquals(
            "Email address (optional - only necessary if you would like us to contact you)",
            self.selenium.get_value('id=id_feedback_dialog_email_address')
        )
        #   * that is grey
        self.assertEquals(self.get_css_property('#id_feedback_dialog_email_address', 'color'), '#808080')
        self.assertEquals(self.get_css_property('#id_feedback_dialog_email_address', 'font-style'), 'italic')

        #   * and ok and cancel buttons
        self.wait_for_element_visibility('id=id_feedback_dialog_ok_button', True)
        self.wait_for_element_visibility('id=id_feedback_dialog_cancel_button', True)

        # * He enters some text into the message field
        MESSAGE = 'Dear Sirs, your product is teh awesomez!!! love ' + self.get_my_username()
        self.selenium.type('id=id_feedback_dialog_text', MESSAGE)

        # * He decides he wants us to be able to thank him for his kind words, so he moves to the
        #   email field
        self.selenium.focus('id=id_feedback_dialog_email_address')

        # * The prompt text disappears, and the field switches to non-italic non-grey text
        self.assertEquals(
            "",
            self.selenium.get_value('id=id_feedback_dialog_email_address')
        )
        self.assertEquals(self.get_css_property('#id_feedback_dialog_email_address', 'color'), '#000000')
        self.assertEquals(self.get_css_property('#id_feedback_dialog_email_address', 'font-style'), 'normal')

        # * He types his email address
        SUBMITTED_EMAIL_ADDRESS = 'harold@mailinator.com'
        self.selenium.type('id=id_feedback_dialog_email_address', SUBMITTED_EMAIL_ADDRESS)

        # * Hits cancel and the form goes away wthout doing anything
        self.selenium.click('id=id_feedback_dialog_cancel_button')
        self.wait_for_element_visibility('id=id_feedback_dialog', False)

        # * this time he means it, so he opens the form again
        self.selenium.click('link=Feedback')
        self.wait_for_element_visibility('id=id_feedback_dialog', True)

        # * His message and email are still there.
        self.assertEquals(
            MESSAGE,
            self.selenium.get_value('id=id_feedback_dialog_text')
        )
        self.assertEquals(
            SUBMITTED_EMAIL_ADDRESS,
            self.selenium.get_value('id=id_feedback_dialog_email_address')
        )

        # He clicks OK.
        self.selenium.click('id=id_feedback_dialog_ok_button')

        # * The dialog goes away
        self.wait_for_element_visibility('id=id_feedback_dialog', False)

        # * support@resolversystems.com receives an email with the text he
        #   entered and his email address
        fromm, to, subject, body = self.pop_email_for_client(
            'harold.testuser-admin@projectdirigible.com',
            content_filter=self.get_my_username()
        )
        self.assertEquals(fromm, 'support@projectdirigible.com')
        self.assertEquals(to, 'harold.testuser-admin@projectdirigible.com')
        self.assertEquals(subject, '[Django] User feedback from Dirigible')
        self.assertTrue(MESSAGE in body)
        self.assertTrue(SUBMITTED_EMAIL_ADDRESS in body)
        self.assertTrue("Page: %s" % (self.browser.current_url,) in body)


    def test_feedback_dialog_from_logged_in_dashboard(self):
        # * Harold logs in to Dirigible
        sheet_id = self.login()

        # * he clicks the feedback link
        self.selenium.click('link=Feedback')
        self.wait_for_element_visibility('id=id_feedback_dialog', True)

        #  * titled:
        self.assertEquals('Help us improve',
            self.get_text('css=.ui-dialog-title')
        )
        #  * with some friendly text:
        self.assertEquals(
            "It's always a pleasure to hear from you!",
            self.get_text('css=#id_feedback_dialog_blurb_big')
        )
        self.assertEquals(
            "Ask us a question, or tell us what you love or hate about Dirigible:",
            self.get_text('css=#id_feedback_dialog_blurb_small')
        )
        #   * with a big freeform input field
        #     which has the focus
        self.wait_for_element_visibility('id=id_feedback_dialog_text', True)
        self.assertTrue(self.is_element_focused('id=id_feedback_dialog_text'))

        #   * There is no email field
        self.wait_for_element_visibility('id=id_feedback_dialog_email_address', False)

        #   * and ok and cancel buttons
        self.wait_for_element_visibility('id=id_feedback_dialog_ok_button', True)
        self.wait_for_element_visibility('id=id_feedback_dialog_cancel_button', True)

        # * He enters some text into the message field
        MESSAGE = 'Dear Sirs, your product is teh awesomez!!! love ' + self.get_my_username()
        self.selenium.type('id=id_feedback_dialog_text', MESSAGE)

        # * Hits cancel and the form goes away wthout doing anything
        self.selenium.click('id=id_feedback_dialog_cancel_button')
        self.wait_for_element_visibility('id=id_feedback_dialog', False)

        # * this time he means it, so he opens the form again
        self.selenium.click('link=Feedback')
        self.wait_for_element_visibility('id=id_feedback_dialog', True)

        # * His message is still there.
        self.assertEquals(
            MESSAGE,
            self.selenium.get_value('id=id_feedback_dialog_text')
        )

        # * He hits OK
        self.selenium.click('id=id_feedback_dialog_ok_button')

        # * The dialog goes away
        self.wait_for_element_visibility('id=id_feedback_dialog', False)

        # * support@resolversystems.com receives an email with the text he
        #   entered and his username
        fromm, to, subject, body = self.pop_email_for_client(
            'harold.testuser-admin@projectdirigible.com',
            content_filter=self.get_my_username()
        )
        self.assertEquals(fromm, 'support@projectdirigible.com')
        self.assertEquals(to, 'harold.testuser-admin@projectdirigible.com')
        self.assertEquals(subject, '[Django] User feedback from Dirigible')
        self.assertTrue(MESSAGE in body)
        self.assertTrue("Username: %s" % (self.get_my_username(),) in body)
        self.assertTrue("Page: %s" % (self.browser.current_url,) in body)


    def test_feedback_dialog_displays_submission_status(self):
        # * Harold is not logged in, and goes to the root Dirigible page.
        self.go_to_url(Url.ROOT)

        self.selenium.get_eval("""
            (function () {
                var oldAjax = window.$.ajax;
                function slowAjax(params) {
                    setTimeout(
                        function() { oldAjax(params); },
                        7000
                    );
                }
                window.$.ajax = slowAjax;
            })()
        """);

        # * he clicks the feedback link
        self.selenium.click('link=Feedback')
        self.wait_for_element_visibility('id=id_feedback_dialog', True)

        # * He enters some text into the message field
        MESSAGE = 'Dear Sirs, your product is teh awesomez!!! love ' + self.get_my_username()
        self.selenium.type('id=id_feedback_dialog_text', MESSAGE)

        # * He types his email address
        SUBMITTED_EMAIL_ADDRESS = 'harold@mailinator.com'
        self.selenium.type('id=id_feedback_dialog_email_address', SUBMITTED_EMAIL_ADDRESS)

        # Something goes wrong with the Dirigible server
        old_feedback_url = self.selenium.get_eval("window.urls.feedback")
        self.selenium.get_eval("window.urls.feedback = 'blergh'")

        # Blissfully unaware of this, Harold clicks OK.
        self.selenium.click('id=id_feedback_dialog_ok_button')

        # The dialog remains, the buttons go disabled
        self.wait_for(
            lambda: not self.is_element_enabled('id_feedback_dialog_ok_button'),
            lambda: 'ok button to become disabled'
        )
        self.wait_for(
            lambda: not self.is_element_enabled('id_feedback_dialog_cancel_button'),
            lambda: 'cancel button to become disabled'
        )

        # an error div appears to tell him that something is wrong.
        self.wait_for_element_visibility('id=id_feedback_dialog', True)
        self.wait_for_element_visibility('id=id_feedback_dialog_error', True)

        # the buttons become enabled again
        self.wait_for(
            lambda: self.is_element_enabled('id_feedback_dialog_ok_button'),
            lambda: 'ok button to become enabled'
        )
        self.wait_for(
            lambda: self.is_element_enabled('id_feedback_dialog_cancel_button'),
            lambda: 'cancel button to become enabled'
        )

        # He waits for a moment, and the server magically fixes itself.
        self.selenium.get_eval("window.urls.feedback = '%s'" % (old_feedback_url,))

        # He tries again.
        self.selenium.click('id=id_feedback_dialog_ok_button')

        # The error message disappears immediately
        self.wait_for_element_visibility('id=id_feedback_dialog_error', False, timeout_seconds=3)

        # * The dialog goes away
        self.wait_for_element_visibility('id=id_feedback_dialog', False)

        # * He brings up the dialog again
        self.selenium.click('link=Feedback')
        self.wait_for_element_visibility('id=id_feedback_dialog', True)

        # * He sees that the buttons are enabled and the error message is absent.
        self.wait_for(
            lambda: self.is_element_enabled('id_feedback_dialog_ok_button'),
            lambda: 'ok button to become enabled'
        )
        self.wait_for(
            lambda: self.is_element_enabled('id_feedback_dialog_cancel_button'),
            lambda: 'cancel button to become enabled'
        )
        self.wait_for_element_visibility('id=id_feedback_dialog_error', False)
