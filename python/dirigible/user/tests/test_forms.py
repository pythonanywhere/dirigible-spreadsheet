# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from registration.forms import RegistrationForm

from dirigible.test_utils import ResolverTestCase
from dirigible.user.forms import DirigibleRegistrationForm


class DirigibleRegistrationFormTest(ResolverTestCase):

    def test_is_registration_form(self):
        form = DirigibleRegistrationForm()
        self.assertTrue(isinstance(form, RegistrationForm))


    def test_error_messages(self):
        form = DirigibleRegistrationForm()
        self.assertEquals(form.fields['username'].error_messages['required'], "Please enter a username.")
        self.assertEquals(form.fields['email'].error_messages['required'], "Please enter your email address.")
        self.assertEquals(form.fields['email'].error_messages['invalid'], "Please enter a valid email address.")
        self.assertEquals(form.fields['password1'].error_messages['required'], "Please enter a password.")
        self.assertEquals(form.fields['password2'].error_messages['required'], "Please enter a password.")
