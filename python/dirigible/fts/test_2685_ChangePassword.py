# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#
import time

from functionaltest import FunctionalTest, USER_PASSWORD


class Test_2685_ChangePassword(FunctionalTest):

    def test_change_password(self):
        # * Harold logs in to Dirigible.
        self.login()

        # He decides to change his password.  He clicks on an appropriate-looking button
        # in his dashboard.
        self.assertFalse(self.selenium.is_visible("id=id_change_password_form"))
        self.selenium.click('id=id_change_password_button')

        # He is presented with a form requiring him to enter his current password once
        # and the new password twice and OK and Cancel buttons.
        self.wait_for_element_visibility("id=id_change_password_form", True)
        self.wait_for_element_visibility("id=id_change_password_current_password", True)
        self.wait_for_element_visibility("id=id_change_password_new_password", True)
        self.wait_for_element_visibility("id=id_change_password_new_password_again", True)
        self.wait_for_element_visibility("id=id_change_password_ok_button", True)
        self.wait_for_element_visibility("id=id_change_password_cancel_button", True)

        # He enters nothing and submits
        self.selenium.click('id=id_change_password_ok_button')

        # He gets an appropriate error.
        self.wait_for_element_text('id=id_change_password_error',
            'Current password incorrect.')

        # He enters the wrong current password and new passwords that are the same.
        self.selenium.type('id=id_change_password_current_password', 'random incorrect password')
        self.selenium.type('id=id_change_password_new_password', 'newpassword')
        self.selenium.type('id=id_change_password_new_password_again', 'newpassword')
        self.selenium.click('id=id_change_password_ok_button')

        # He gets an appropriate error.
        self.wait_for_element_text('id=id_change_password_error',
            'Current password incorrect.')

        # He enters the right current password and two different new passwords
        self.selenium.type('id=id_change_password_current_password', USER_PASSWORD)
        self.selenium.type('id=id_change_password_new_password', 'newpassword')
        self.selenium.type('id=id_change_password_new_password_again', 'newpassword different')
        self.selenium.click('id=id_change_password_ok_button')

        # He gets an appropriate error.
        self.wait_for_element_text('id=id_change_password_error',
            'Please provide the new password twice for confirmation.')

        # He gives up in frustration and hits a cancel button on the form.
        self.selenium.click('id=id_change_password_cancel_button')

        # The password change form disappears
        self.wait_for(
            lambda: not self.selenium.is_visible("id=id_change_password_form"),
            lambda: "password change form to hide"
        )

        # and the button re-appears
        self.wait_for_element_visibility('id=id_change_password_button', True)

        # He opens the form again and notes that his old error message is gone and the password fields have been reset
        self.selenium.click('id=id_change_password_button')
        self.wait_for_element_text('id=id_change_password_error', '')
        self.assertEquals(self.selenium.get_value('id=id_change_password_current_password'), '')
        self.assertEquals(self.selenium.get_value('id=id_change_password_new_password'), '')
        self.assertEquals(self.selenium.get_value('id=id_change_password_new_password_again'), '')

        # He logs out.
        self.logout()

        # After tea and consolation from a sympathetic Harriet, he decides to try again.
        # He logs in using his original password.
        self.login()

        # He clicks the change password button.
        self.selenium.click('id=id_change_password_button')

        # This time he manages to get his old password right and enters the
        # same new password both times.
        self.selenium.type('id=id_change_password_current_password', USER_PASSWORD)
        self.selenium.type('id=id_change_password_new_password', 'newpassword')
        self.selenium.type('id=id_change_password_new_password_again', 'newpassword')
        self.selenium.click('id=id_change_password_ok_button')

        # After a few seconds, the form goes away
        self.wait_for(
            lambda: not self.selenium.is_visible("id=id_change_password_form"),
            lambda: "password change form to hide"
        )

        # He is told "thank you".
        self.wait_for_element_visibility("id=id_change_password_success", True)
        self.wait_for_element_text('id=id_change_password_success',
            'Your password has been changed.')

        # then after a couple of seconds, the thank-you goes away
        self.wait_for(
            lambda: not self.selenium.is_visible("id=id_change_password_success"),
            lambda: "password change success notice to hide",
            timeout_seconds=6
        )

        # He logs out
        self.logout()

        # He tries to log in with the old password.
        self.login()

        # It doesn't work.
        self.wait_for_element_text("id=id_login_error",
            "The user name or password is incorrect. Please try again.")

        # He tries the new password.
        self.login(password='newpassword')

        # It works.
        expected = "%s's Dashboard: Dirigible" % (self.get_my_username(),)
        self.assertEquals(self.selenium.get_title(), expected)

        # He celebrates.

