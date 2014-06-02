# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from urlparse import urlparse

from mock import Mock, patch, sentinel

import django
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect

from dirigible.test_utils import assert_security_classes_exist, ResolverTestCase

from dirigible.user.views import (
    change_password, copy_sheet_for_new_user_callback, redirect_to_front_page,
    register, registration_complete, user_dashboard
)
from dirigible.sheet.models import copy_sheet_to_user, Sheet


def set_up_view_test(self):
    self.user = User(username='userviewtestuser')
    self.user.set_password('p455w0rd')
    self.user.save()
    self.request = HttpRequest()
    self.request.user = self.user
    self.request.META['SERVER_NAME'] = ''


class RedirectToFrontPageTest(django.test.TestCase):

    setUp = set_up_view_test

    def test_redirects_to_user_page_when_logged_in(self):
        response = redirect_to_front_page(self.request)

        self.assertTrue(isinstance(response, HttpResponseRedirect))

        redirect_url = urlparse(response['Location'])
        self.assertEquals(redirect_url.path, reverse('front_page'))


class UserDashboardSecurityTest(django.test.TestCase):

    setUp = set_up_view_test

    def test_view_login_required(self):
        request = HttpRequest()
        request.user = AnonymousUser()
        request.META['SERVER_NAME'] = ''
        request.META['SERVER_PORT'] = ''
        actual = user_dashboard(request)

        self.assertTrue(isinstance(actual, HttpResponseRedirect))

        redirect_url = urlparse(actual['Location'])
        self.assertEquals(redirect_url.path, settings.LOGIN_URL)


class UserDashboardTest(django.test.TestCase):

    setUp = set_up_view_test

    def test_page_should_return_response_for_logged_in_owner(self):
        actual = user_dashboard(self.request)
        self.assertTrue(isinstance(actual, HttpResponse))

    @patch('dirigible.user.views.render_to_response')
    def test_userpage_has_list_of_sheets(self, mock_render_to_response):
        sheets = [
            Sheet(owner=self.user),
            Sheet(owner=self.user),
            Sheet(owner=self.user),
        ]
        map(lambda x: x.save(), sheets)

        user_dashboard(self.request)

        objects_passed_to_template = mock_render_to_response.call_args[0][1]
        self.assertTrue('sheets' in objects_passed_to_template)
        passed_sheet_ids = [s.id for s in objects_passed_to_template['sheets']]
        self.assertEquals(set(passed_sheet_ids), set(s.id for s in sheets))



class ChangePasswordSecurityTest(django.test.TestCase):

    setUp = set_up_view_test

    def test_view_should_raise_on_wrong_user(self):
        wrong_user = User(username='validbutnotowner')
        wrong_user.save()
        self.assertRaises(Http404, change_password, self.request, wrong_user.username)


    def test_view_404_errors_should_be_indistinguishable(self):
        # We don't want users to be able to detect whether other users with particular names
        # exist, so 404 from nonexistent users' pages should be indistinguishable from 404
        # from trying to access existing users' pages.
        e1 = None
        try:
            change_password(self.request, "nonexistent_user")
        except Http404, e1:
            pass

        existing_user = User(username='existing_user')
        existing_user.save()
        e2 = None
        try:
            change_password(self.request, existing_user.username)
        except Http404, e2:
            pass

        self.assertEquals(str(e1), str(e2))


    def test_view_login_required(self):
        request = HttpRequest()
        request.META['SERVER_NAME'] = ''
        request.META['SERVER_PORT'] = ''
        request.user = AnonymousUser()
        actual = change_password(request, self.user.username)

        self.assertTrue(isinstance(actual, HttpResponseRedirect))

        redirect_url = urlparse(actual['Location'])
        self.assertEquals(redirect_url.path, settings.LOGIN_URL)


    def test_view_should_raise_if_nonexistent_user(self):
        self.assertRaises(Http404, change_password, self.request, 'baduser')


class ChangePasswordTest(django.test.TestCase):

    setUp = set_up_view_test

    def test_change_password_with_empty_fields(self):
        actual = change_password(self.request, self.user.username)

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, 'Current password incorrect.')


    def test_change_password_with_wrong_old_password(self):
        self.request.POST['id_change_password_current_password'] = 'wrongpassword'
        self.request.POST['id_change_password_new_password'] = '1234'
        self.request.POST['id_change_password_new_password_again'] = '1234'

        actual = change_password(self.request, self.user.username)

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, 'Current password incorrect.')


    def test_change_password_with_differing_new_passwords(self):
        self.request.POST['id_change_password_current_password'] = 'p455w0rd'
        self.request.POST['id_change_password_new_password'] = '1234'
        self.request.POST['id_change_password_new_password_again'] = '12345'

        actual = change_password(self.request, self.user.username)

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, 'Please provide the new password twice for confirmation.')


    def test_change_password_does(self):
        self.request.POST['id_change_password_current_password'] = 'p455w0rd'
        self.request.POST['id_change_password_new_password'] = '1234'
        self.request.POST['id_change_password_new_password_again'] = '1234'

        actual = change_password(self.request, self.user.username)

        self.assertTrue(isinstance(actual, HttpResponse))
        self.assertEquals(actual.content, 'Your password has been changed.')

        updated_user = User.objects.get(pk=self.user.id)
        self.assertTrue(updated_user.check_password('1234'))


class RegistrationViewsTest(ResolverTestCase):

    @patch('dirigible.user.views.DirigibleRegistrationForm')
    @patch('dirigible.user.views.django_registration')
    def test_register_puts_email_address_into_session_if_form_is_valid(self, mock_registration_module, mock_form_class):
        """
        There seems to be no way of getting the user's details from the
        registration confirmation page in the default django-registration
        system.  So we wrap it with our own code to stuff the important
        bits into the session.
        """
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = { 'email' : sentinel.email }

        mock_request = Mock()
        mock_request.session = {}
        mock_request.POST = []
        mock_request.GET = {}

        register(mock_request)

        self.assertEquals(mock_request.session['email-address'], sentinel.email)


    @patch('dirigible.user.views.copy_sheet_to_user')
    def test_copy_sheet_for_new_user_callback_copies_sheet_specified_in_next_url(self, mock_copy_sheet_to_user):
        from_user = User(username='from_user')
        from_user.save()

        to_user = User(username='to_user')
        to_user.save()

        from_sheet = Sheet(owner=from_user)
        from_sheet.save()
        next_url = '/user/admin/sheet/%s/copy_sheet/' % (from_sheet.id,)

        callback = copy_sheet_for_new_user_callback(next_url)
        callback(to_user)

        self.assertCalledOnce(mock_copy_sheet_to_user, from_sheet, to_user)


    @patch('dirigible.user.views.DirigibleRegistrationForm')
    @patch('dirigible.user.views.django_registration')
    def test_register_doesnt_put_email_address_into_session_if_form_is_not_valid(self, mock_registration_module, mock_form_class):
        """
        There seems to be no way of getting the user's details from the
        registration confirmation page in the default django-registration
        system.  So we wrap it with our own code to stuff the important
        bits into the session.
        """
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = False

        mock_request = Mock()
        mock_request.session = {}
        mock_request.POST = []
        mock_request.GET = {}

        register(mock_request)

        self.assertTrue('email-address' not in mock_request.session)


    @patch('dirigible.user.views.DirigibleRegistrationForm')
    @patch('dirigible.user.views.django_registration')
    @patch('dirigible.user.views.copy_sheet_for_new_user_callback')
    def test_register_delegates_to_django_registration_with_form(self, mock_copy_sheet_callback, mock_registration_module, mock_form_class):
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = False

        mock_request = Mock()
        mock_request.POST = {}
        mock_request.POST['next'] = 'next_page'

        mock_callback = Mock()
        mock_copy_sheet_callback.return_value = mock_callback

        response = register(mock_request)

        self.assertCalledOnce(mock_copy_sheet_callback, 'next_page')

        self.assertCalledOnce(
            mock_registration_module.views.register,
            mock_request,
            profile_callback=mock_callback,
            form_class=mock_form_class
        )
        self.assertEquals(
            response,
            mock_registration_module.views.register.return_value
        )


    @patch('dirigible.user.views.DirigibleRegistrationForm')
    @patch('dirigible.user.views.django_registration')
    def test_register_provides_extra_context_only_if_its_provided(self, mock_registration_module, mock_form_class):
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = False

        mock_request = Mock()
        mock_request.POST = {}
        mock_request.GET = {}

        register(mock_request)

        self.assertCalledOnce(
            mock_registration_module.views.register,
            mock_request,
            form_class=mock_form_class
        )

        mock_registration_module.views.register.reset_mock()
        mock_request.GET['next'] = 'next_page'

        register(mock_request)

        self.assertCalledOnce(
            mock_registration_module.views.register,
            mock_request,
            form_class=mock_form_class,
            extra_context={'next': 'next_page'}
        )



    @patch('dirigible.user.views.direct_to_template')
    def test_registration_complete_renders_template_with_email_address_from_session(self, mock_direct_to_template):
        """
        There seems to be no way of getting the user's details from the
        registration confirmation page in the default django-registration
        system.  So we wrap it with our own code to stuff the important
        bits into the session.
        """
        mock_request = Mock()
        mock_request.session = { 'email-address' : sentinel.email_address }
        response = registration_complete(mock_request)
        self.assertCalledOnce(
            mock_direct_to_template,
            mock_request,  'registration/registration_complete.html',
            extra_context={ 'email_address' : sentinel.email_address }
        )
        self.assertEquals(response, mock_direct_to_template.return_value)



    @patch('dirigible.user.views.direct_to_template')
    def test_registration_complete_renders_template_with_blank_email_address_if_none_in_session(self, mock_direct_to_template):
        """
        There seems to be no way of getting the user's details from the
        registration confirmation page in the default django-registration
        system.  So we wrap it with our own code to stuff the important
        bits into the session.
        """
        mock_request = Mock()
        mock_request.session = {}
        response = registration_complete(mock_request)
        self.assertCalledOnce(
            mock_direct_to_template,
            mock_request,  'registration/registration_complete.html',
            extra_context={ 'email_address' : None }
        )
        self.assertEquals(response, mock_direct_to_template.return_value)


class MetaSecurityTest(django.test.TestCase):
    def test_security_classes_exist(self):
        assert_security_classes_exist(
            self, __name__,
            ['RedirectToFrontPageTest', 'RegistrationViewsTest', 'ResolverTestCase']
        )

