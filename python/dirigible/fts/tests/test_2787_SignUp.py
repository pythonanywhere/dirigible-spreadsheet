# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import re
from urlparse import urlparse, urljoin
import key_codes

from browser_settings import SERVER_IP
from functionaltest import FunctionalTest, Url


class Test_2787_SignUp(FunctionalTest):

    def are_password_fields_showing_error(self):
        return (
            self.selenium.is_element_present('css=#id_password1.error')
            and self.selenium.is_element_present('css=#id_password2.error')
        )


    def test_can_sign_up_from_signup_page(self):
        # Harold goes to the Dirigible home page
        self.go_to_url('/')

        # He notes that there are two "sign up" links, both pointing to the same URL
        self.click_link("id_signup_link")
        signup_url = self.browser.current_url
        self.go_to_url('/')

        # He follows one of them
        self.click_link("id_signup_call_to_action")
        self.assertEquals(self.browser.current_url, signup_url)

        # He notices a "sign up" form that requires a username, an email address,
        # and two copies of the same password.
        self.assertTrue(self.selenium.is_element_present(
            'css=input#id_username'))
        self.assertTrue(self.selenium.is_element_present(
            'css=input#id_email'))
        self.assertTrue(self.selenium.is_element_present(
            'css=input#id_password1'))
        self.assertTrue(self.selenium.is_element_present(
            'css=input#id_password2'))
        self.assertTrue(self.selenium.is_element_present(
            'css=input#id_signup_button'))
        self.assertEquals(
            self.selenium.get_attribute(
                'css=#id_signup_button@value'),
            'Sign up')
        self.assertEquals(
            self.selenium.get_attribute(
                'css=input#id_signup_button@type'),
            'submit')

        # Being an awkward sod, he tries to sign up with no details.
        self.click_link('id_signup_button')

        # He is told off.
        self.assertEquals(
            self.get_text('id=id_username_error'),
            "Please enter a username."
        )
        self.assertEquals(
            self.get_text('id=id_email_error'),
            "Please enter your email address."
        )
        self.assertEquals(
            self.get_text('id=id_password1_error'),
            "Please enter a password."
        )
        self.assertEquals(
            self.get_text('id=id_password2_error'),
            "Please enter a password."
        )

        # He tries again, this time using his friend's username,
        # but entering sensible details for everything else.
        username = self.get_my_username() + "_x"
        duplicate_username = self.get_my_username()
        self.email_address = 'harold.testuser-%s@resolversystems.com' % (self.get_my_username(),)
        password = 'p4ssw0rd'
        self.selenium.type(
            'id=id_username',
            duplicate_username)
        self.selenium.type(
            'id=id_email',
            self.email_address)
        self.selenium.type(
            'id=id_password1',
            password)
        self.selenium.type(
            'id=id_password2',
            password)
        self.click_link('id_signup_button')

        # He is told off.
        self.assertEquals(
            self.get_text('id=id_username_error'),
            "This username is already taken. Please choose another."
        )

        # He tries again with a unique username but mistypes the email address
        self.selenium.type(
            'id=id_username',
            username)
        self.selenium.type(
            'id=id_email',
            '@@@@@')
        self.selenium.type(
            'id=id_password1',
            password)
        self.selenium.type(
            'id=id_password2',
            password)
        self.click_link('id_signup_button')

        # He is told off.
        self.assertEquals(
            self.get_text('id=id_email_error'),
            "Please enter a valid email address."
        )

        # He tries again with a unique username but mistypes the password
        self.selenium.type(
            'id=id_username',
            username)
        self.selenium.type(
            'id=id_email',
            self.email_address)
        self.selenium.type(
            'id=id_password1',
            password)
        self.selenium.type(
            'id=id_password2',
            "hello")
        ## Do the last character using native keypresses to make sure that
        ## all of our client-side validation JS really gets called
        self.selenium.focus('id=id_password2')
        self.human_key_press(key_codes.NUMBER_1)

        # Even before he submits the form, the page is grumbling at him
        self.wait_for(
            self.are_password_fields_showing_error,
            lambda : "Password error to appear"
        )

        # With misplaced self-confidence, he goes ahead and clicks the button
        self.click_link('id_signup_button')

        # He is told off.
        self.assertEquals(
            self.get_text('id=id_non_field_errors'),
            "You must type the same password each time"
        )

        # He finally does it correctly
        self.selenium.type(
            'id=id_username',
            username)
        self.selenium.type(
            'id=id_email',
            self.email_address)
        self.selenium.type(
            'id=id_password1',
            password)
        self.selenium.type(
            'id=id_password2',
            password)

        # Before he clicks the link, he confirms that there is no error in the password fields
        self.wait_for(
            lambda : not self.are_password_fields_showing_error(),
            lambda : "Password errors to not be there"
        )

        self.click_link('id_signup_button')

        # He gets a message saying "Thank you" that tells him that an email has been
        # sent to his address.
        self.assertTrue('Thank you' in self.selenium.get_body_text())
        self.assertTrue(self.email_address in self.selenium.get_body_text())

        # There is a link to the Dirigible home page, which he follows and discovers
        # that it works.
        self.click_link('id_link_home')
        self.assertEquals(self.browser.current_url, Url.ROOT)

        # He checks his email, and after a short wait finds a message
        # from the Dirigible server, that looks like the following string:
        email_from, email_to, subject, message = self.pop_email_for_client(self.email_address)
        self.assertEquals(email_to, self.email_address)
        self.assertEquals(email_from, 'support@projectdirigible.com')
        self.assertEquals(subject, 'Dirigible Beta Sign-up')
        self.assertTrue('Click on the following link' in message)
        confirm_url_re = re.compile(
            r'<(http://projectdirigible\.com/signup/activate/[^>]+)>')
        match = confirm_url_re.search(message)
        self.assertTrue(match)
        confirmation_url = match.group(1).replace('projectdirigible.com', SERVER_IP)

        # He decides to type the confirmation link manually into his browser and,
        # inevitably, gets it completely wrong
        self.go_to_url(urljoin(Url.ROOT, '/signup/activate/wibble'))

        # He's given a kindly warning.
        self.assertTrue('the activation link you used was not recognised' in self.selenium.get_body_text())

        # He clicks on the link in the email instead
        self.go_to_url(confirmation_url)

        body_text = self.selenium.get_body_text()
        # He's taken to a page that welcomes him aboard and allows him to log in.
        self.assertTrue(
            'Welcome to Dirigible' in body_text,
            'could not find "Welcome to Dirigible" on page.  URL:<%s>, body text:\n%s' % (confirmation_url, body_text[:-100])
        )

        # He logs in, using the fields on the page.
        self.login(username, password, already_on_login_page=True)

        # He is taken to his dashboard
        self.assertEquals(self.selenium.get_title(), "%s's Dashboard: Dirigible" % (username,))
        _, __, path, ___, ____, _____ = urlparse(self.browser.current_url)
        self.assertEquals(path, '/')

        # He's super keen to get in on the Dirigible action, so when he sees the
        # link saying "Create new sheet", he clicks it with gusto
        self.click_link('id_create_new_sheet')

        # He sees a dialog box promoting the tutorial
        self.wait_for_element_visibility('id_tutorial_promo_dialog', True)
        dialog_text = self.get_text('id=id_tutorial_promo_dialog')
        self.assertTrue('tutorial' in dialog_text.lower())

        # He notes that even when the spinner stops, the focus stays on the dialog's OK
        # button
        self.wait_for_spinner_to_stop()
        self.assertTrue(
                self.is_element_focused('css=#id_tutorial_promo_dialog_close')
        )

        # He notices a link to the tutorial inside the dialog
        tutorial_link_inside_dialog_locator = 'css=#id_tutorial_promo_dialog a#id_tutorial_link'
        self.wait_for_element_to_appear(tutorial_link_inside_dialog_locator)
        tutorial_link_url = self.selenium.get_attribute('%s@href' % (tutorial_link_inside_dialog_locator))

        # He clicks the OK button to dismiss the dialog
        self.selenium.click('id=id_tutorial_promo_dialog_close')

        # the dialog disappears
        self.wait_for_element_visibility('id=id_tutorial_promo_dialog', False)

        # he goes to the tutorial url he remembers from earlier
        self.go_to_url(tutorial_link_url)

        # He finds himself on a page which contains the first tutorial
        expected_title = 'Tutorial part 1: First steps, adding Python to a spreadsheet'
        self.assertTrue(expected_title in self.selenium.get_title())

        # He goes back to the dashboard
        self.go_to_url(Url.ROOT)

        # He creates another sheet, ready to get annoyed if he sees that dialog again...
        self.click_link('id_create_new_sheet')

        # And is happy that it isn't there,
        self.wait_for_grid_to_appear()
        self.assertFalse(
                self.selenium.is_element_present('id=id_tutorial_promo_dialog')
        )

        # He logs out
        self.logout()

        # He decides that he enjoyed confirming his account so much, he'd like to
        # do it again.
        self.go_to_url(confirmation_url)

        # He's given a kindly warning.
        self.assertTrue('your account might already be activated' in self.selenium.get_body_text())

        # When he returns to his email app, he sees a second email from us,
        email_from, email_to, subject, message = self.pop_email_for_client(self.email_address)
        self.assertEquals(email_to, self.email_address)
        self.assertEquals(email_from, 'support@projectdirigible.com')
        self.assertEquals(subject, 'Welcome to Dirigible')

        # pointing him towards the tutorial.
        self.assertTrue('tutorial' in message.lower())
        self.assertTrue('/documentation/tutorial01.html' in message)

        # We also recommend that he subscribe to the Dirigible blog
        self.assertTrue('blog.projectdirigible.com' in message)

        # or follows us on Twitter
        self.assertTrue('twitter.com/dirigiblegrid' in message)

        # Satisfied, he goes back to sleep.
        self.assertTrue('sleep')

