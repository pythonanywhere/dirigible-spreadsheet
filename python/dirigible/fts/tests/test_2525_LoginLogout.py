# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from urlparse import urlparse

from functionaltest import FunctionalTest, snapshot_on_error, Url


class Test_2525_LoginLogout(FunctionalTest):

    user_count = 2

    def assert_login_error_shown(self):
        self.assertEquals(
            self.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again."
        )


    @snapshot_on_error
    def test_login(self):
        # Harold goes to a specific URL.
        self.go_to_url(Url.LOGIN)

        # He sees a web page with "Login: Dirigible" in the title bar.
        self.assertEquals(self.browser.title, 'Login: Dirigible')
        welcome_url = self.browser.current_url

        # and notices that his cursor is in the username field
        self.assertTrue(self.is_element_focused('id=id_username'))

        # He sees links to the terms and conditions and suchlike at the bottom of the page.
        self.assert_has_useful_information_links()

        # He notices a login link on the page and sees that it leads back to this page
        login_link = self.get_element('css=a#id_login_link')
        self.assertEqual(login_link.get_attribute('href'), Url.LOGIN)

        # There is also a "sign up" link that would take him to the signup page.
        signup_link = self.get_element('css=a#id_signup_link')
        self.assertEqual(signup_link.get_attribute('href'), Url.SIGNUP)

        # The page also contains places where he can enter a user name and a password, and
        # a login button.
        self.get_element('css=input#id_username')
        self.get_element('css=input#id_password')
        self.get_element('css=input#id_login[type=submit]')

        # He enters neither, and clicks the login button.
        self.click_link('id_login')

        # He is taken back to a copy of the login page where he is additionally chided for
        # not entering his details.
        self.assert_login_error_shown()

        # He enters a username but no password
        self.get_element('id=id_username').send_keys('confused_user')
        self.click_link('id_login')

        # He is taken back to a copy of the login page where he is told he must enter a
        # password.  The username is still there.
        self.assert_login_error_shown()
        self.assertEquals(self.get_text('id=id_username'), 'confused_user')

        # He enters a password but no username
        self.get_element('id=id_username').clear()
        self.get_element('id=id_password').send_keys('confused_pass')
        self.click_link('id_login')

        # He is taken back to a copy of the login page that patiently reminds him that he
        # should enter a username.  The password is still there (albeit masked by *s)
        self.assert_login_error_shown()
        self.assertEquals(self.get_text('id=id_username'), '')
        self.assertEquals(self.get_text('id=id_password'), 'confused_pass')

        # He enters the wrong username and password
        self.get_element('id=id_username').send_keys('wrong user')
        self.get_element('id=id_password').send_keys('wrong password')
        self.click_link('id_login')

        # He is taken back to a copy of the login page telling him that the username/password
        # combo wasn't recognised.  Both username and masked password are still there.
        self.assert_login_error_shown()
        self.assertEquals(self.get_text('id=id_username'), 'wrong user')
        self.assertEquals(self.get_text('id=id_password'), 'wrong password')

        # He corrects the username, but enters the wrong password
        username = self.get_my_username()
        self.get_element('id=id_username').send_keys(username)
        self.get_element('id=id_password').send_keys('wrong password')
        self.click_link('id_login')

        # He is taken back to a copy of the login page telling him that the username/password
        # combo wasn't recognised.  Both username and masked password are still there.
        self.assert_login_error_shown()
        self.assertEquals(self.get_text('id=id_username'), username)
        self.assertEquals(self.get_text('id=id_password'), 'wrong password')

        # He enters the correct password, but takes the opportunity to make the username
        # incorrect.
        self.get_element('id=id_username').send_keys('wrong user')
        self.assertEquals(self.get_text('id=id_password'), 'p4ssw0rd')
        self.click_link('id_login')

        # He is taken back to a copy of the login page telling him that the username/password
        # combo wasn't recognised.  Both username and masked password are still there.
        self.assert_login_error_shown()
        self.assertEquals(self.get_text('id=id_username'), 'wrong user')
        self.assertEquals(self.get_text('id=id_password'), 'p4ssw0rd')

        # Finally, he enters the correct username and password.
        self.get_element('id=id_username').send_keys(username)
        self.get_element('id=id_password').send_keys('p4ssw0rd')
        self.click_link('id_login')

        # He is taken to a page entitled "XXXX's Dashboard: Dirigible" at the site's root URL.
        self.assertEquals(
            self.browser.title,
            "{}'s Dashboard: Dirigible".format(username)
        )
        _, __, path, ___, ____, _____ = urlparse(self.browser.current_url)
        self.assertEquals(path, '/')

        # He sees links to the terms and conditions and suchlike at the bottom of the page.
        self.assert_has_useful_information_links()

        # On the page is a "Log Out" link
        self.assertEquals(self.get_text('id=id_logout_link'), "Log out")

        # He follows it.
        self.click_link('id_logout_link')

        # He is taken back to the "Login: Dirigible" page he saw at the start of this FT.
        self.assertEquals(self.browser.current_url, welcome_url)
        self.assertEquals(self.browser.title, 'Login: Dirigible')

        # He logs in again
        self.get_element('id=id_username').send_keys(username)
        self.get_element('id=id_password').send_keys('p4ssw0rd')
        self.click_link('id_login')

        # He goes back to the login page and is presented with the option to login
        # and the page also includes 'My account' and 'Logout' links
        self.go_to_url(Url.LOGIN)
        self.get_element('css=input#id_username')
        self.get_element('css=input#id_password')
        self.assertEquals(self.get_text('id=id_logout_link'), "Log out")
        self.assertEquals(self.get_text('id=id_account_link'), "My account")

        # He is satisfied, and calls it a day.


    def test_legacy_dashboard_link_takes_you_to_root_url(self):
        harriet = self.get_my_usernames()[1]
        harold = self.get_my_username()
        harolds_dashboard_url = '/user/%s/' % (harold,)
        harriets_dashboard_url = '/user/%s/' % (harriet,)

        # Before logging in, Harold tries to access his own dashboard using the
        # old-style URL.
        # He gets sent to the root page.
        self.assert_sends_to_root_page(harolds_dashboard_url)

        # Before logging in, Harold tries to access Harriet's dashboard using the
        # old-style URL.
        # He gets redirected to the root page
        self.assert_sends_to_root_page(harriets_dashboard_url)

        # Before logging in, Harold also tries to access a non-existent user's dashboard using the
        # old-style URL.
        # He gets sent to the root page.
        self.assert_sends_to_root_page('/user/non-existent-user/')

        # After logging in, Harold tries to access his own dashboard using the
        # old-style URL.
        # He gets sent to the root page.
        self.login(username=harold)
        self.assert_sends_to_root_page(harolds_dashboard_url)

        # After logging in, Harold tries to access Harriet's dashboard using the
        # old-style URL.
        # He gets sent to the root page.
        self.assert_sends_to_root_page(harriets_dashboard_url)

        # After logging in, Harold also tries to access a non-existent user's dashboard using the
        # old-style URL.
        # He gets sent to the root page.
        self.assert_sends_to_root_page('/user/non-existent-user/')
