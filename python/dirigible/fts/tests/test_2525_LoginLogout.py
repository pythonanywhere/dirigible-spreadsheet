# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from urlparse import urlparse

from functionaltest import FunctionalTest, snapshot_on_error, Url


class Test_2525_LoginLogout(FunctionalTest):

    user_count = 2


    @snapshot_on_error
    def test_login(self):
        # Harold goes to a specific URL.
        self.go_to_url(Url.LOGIN)

        # He sees a web page with "Login: Dirigible" in the title bar.
        self.assertEquals(self.selenium.get_title(), 'Login: Dirigible')
        welcome_url = self.selenium.get_location()

        # and notices that his cursor is in the username field
        self.assertTrue(self.is_element_focused('id=id_username'))

        # He sees links to the terms and conditions and suchlike at the bottom of the page.
        self.assert_has_useful_information_links()        

        # He notices a login link on the page and sees that it leads back to this page
        self.assertTrue(self.selenium.is_element_present('css=a#id_login_link'))
        self.assert_urls_are_same(
            self.selenium.get_attribute('css=#id_login_link@href'),
            Url.LOGIN
        )

        # There is also a "sign up" link that would take him to the signup page.
        self.assertTrue(self.selenium.is_element_present('css=a#id_login_link'))
        self.assert_urls_are_same(
            self.selenium.get_attribute('css=#id_signup_link@href'),
            Url.SIGNUP
        )

        # The page also contains places where he can enter a user name and a password, and
        # a login button.
        self.assertTrue(self.selenium.is_element_present('css=input#id_username'))
        self.assertTrue(self.selenium.is_element_present('css=input#id_password'))
        self.assertEquals(self.selenium.get_attribute('css=#id_password@type'),
            'password')
        self.assertTrue(self.selenium.is_element_present('css=input#id_login'))
        self.assertEquals(self.selenium.get_attribute('css=#id_login@value'),
            'Login')
        self.assertEquals(self.selenium.get_attribute('css=#id_login@type'),
            'submit')

        # He enters neither, and clicks the login button.
        self.click_link('id_login')

        # He is taken back to a copy of the login page where he is additionally chided for
        # not entering his details.
        self.assertEquals(self.selenium.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again.")

        # He enters a username but no password
        self.selenium.type('id=id_username', 'confused_user')
        self.click_link('id_login')

        # He is taken back to a copy of the login page where he is told he must enter a
        # password.  The username is still there.
        self.assertEquals(self.selenium.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again.")
        self.assertEquals(self.selenium.get_value('id=id_username'), 'confused_user')

        # He enters a password but no username
        self.selenium.type('id=id_username', '')
        self.selenium.type('id=id_password', 'confused_pass')
        self.click_link('id_login')

        # He is taken back to a copy of the login page that patiently reminds him that he
        # should enter a username.  The password is still there (albeit masked by *s)
        self.assertEquals(self.selenium.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again.")
        self.assertEquals(self.selenium.get_value('id=id_username'), '')
        self.assertEquals(self.selenium.get_value('id=id_password'), 'confused_pass')

        # He enters the wrong username and password
        self.selenium.type('id=id_username', 'wrong_user')
        self.selenium.type('id=id_password', 'wrong_pass')
        self.click_link('id_login')

        # He is taken back to a copy of the login page telling him that the username/password
        # combo wasn't recognised.  Both username and masked password are still there.
        self.assertEquals(self.selenium.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again.")
        self.assertEquals(self.selenium.get_value('id=id_username'), 'wrong_user')
        self.assertEquals(self.selenium.get_value('id=id_password'), 'wrong_pass')

        # He corrects the username, but enters the wrong password
        self.selenium.type('id=id_username', self.get_my_username())
        self.selenium.type('id=id_password', 'wrong_pass')
        self.click_link('id_login')

        # He is taken back to a copy of the login page telling him that the username/password
        # combo wasn't recognised.  Both username and masked password are still there.
        self.assertEquals(self.selenium.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again.")
        self.assertEquals(self.selenium.get_value('id=id_username'), self.get_my_username())
        self.assertEquals(self.selenium.get_value('id=id_password'), 'wrong_pass')

        # He enters the correct password, but takes the opportunity to make the username
        # incorrect.
        self.selenium.type('id=id_username', 'wrong_user')
        self.selenium.type('id=id_password', 'p4ssw0rd')
        self.click_link('id_login')

        # He is taken back to a copy of the login page telling him that the username/password
        # combo wasn't recognised.  Both username and masked password are still there.
        self.assertEquals(self.selenium.get_text('id=id_login_error'),
            "The user name or password is incorrect. Please try again.")
        self.assertEquals(self.selenium.get_value('id=id_username'), 'wrong_user')
        self.assertEquals(self.selenium.get_value('id=id_password'), 'p4ssw0rd')

        # Finally, he enters the correct username and password.
        self.selenium.type('id=id_username', self.get_my_username())
        self.selenium.type('id=id_password', 'p4ssw0rd')
        self.click_link('id_login')

        # He is taken to a page entitled "XXXX's Dashboard: Dirigible" at the site's root URL.
        self.assertEquals(self.selenium.get_title(), "%s's Dashboard: Dirigible" % (self.get_my_username(),))
        _, __, path, ___, ____, _____ = urlparse(self.selenium.get_location())
        self.assertEquals(path, '/')

        # He sees links to the terms and conditions and suchlike at the bottom of the page.
        self.assert_has_useful_information_links()
        
        # On the page is a "Log Out" link
        self.assertEquals(self.selenium.get_text('id=id_logout_link'),
            "Log out")

        # He follows it.
        self.click_link('id_logout_link')

        # He is taken back to the "Login: Dirigible" page he saw at the start of this FT.
        self.assertEquals(self.selenium.get_location(), welcome_url)
        self.assertEquals(self.selenium.get_title(), 'Login: Dirigible')

        # He logs in again
        self.selenium.type('id=id_username', self.get_my_username())
        self.selenium.type('id=id_password', 'p4ssw0rd')
        self.click_link('id_login')

        # He goes back to the login page and is presented with the option to login
        # and the page also includes 'My account' and 'Logout' links
        self.go_to_url(Url.LOGIN)
        self.assertTrue(self.selenium.is_element_present('css=input#id_username'))
        self.assertTrue(self.selenium.is_element_present('css=input#id_password'))
        self.assertEquals(self.selenium.get_text('id=id_logout_link'),
                          "Log out")
        self.assertEquals(self.selenium.get_text('id=id_account_link'),
                          "My account")

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
