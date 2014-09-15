# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from registration.forms import RegistrationForm


class DirigibleRegistrationForm(RegistrationForm):
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args,  **kwargs)
        self.fields['username'].error_messages['required'] = 'Please enter a username.'
        self.fields['email'].error_messages['required'] = 'Please enter your email address.'
        self.fields['email'].error_messages['invalid'] = 'Please enter a valid email address.'
        self.fields['password1'].error_messages['required'] = 'Please enter a password.'
        self.fields['password2'].error_messages['required'] = 'Please enter a password.'
