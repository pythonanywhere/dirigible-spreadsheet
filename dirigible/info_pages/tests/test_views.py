# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from mock import patch, sentinel, Mock

from dirigible.test_utils import ResolverTestCase

from info_pages.views import front_page_view, info_page_view, non_logged_in_front_page_view


class TestFrontPageView(ResolverTestCase):

    @patch('info_pages.views.non_logged_in_front_page_view')
    def test_should_delegate_to_non_logged_in_front_page_view_if_not_logged_in(self, mock_non_logged_in_front_page_view):
        request = Mock()
        request.user.is_authenticated.return_value = False
        response = front_page_view(request)
        self.assertCalledOnce(mock_non_logged_in_front_page_view, request)
        self.assertEquals(response, mock_non_logged_in_front_page_view.return_value)


    @patch('info_pages.views.user_dashboard')
    def test_should_delegate_to_user_dashboard_if_are_logged_in(self, mock_user_dashboard):
        request = Mock()
        request.user.is_authenticated.return_value = True
        response = front_page_view(request)
        self.assertCalledOnce(mock_user_dashboard, request)
        self.assertEquals(response, mock_user_dashboard.return_value)



class TestNonLoggedInFrontPageView(ResolverTestCase):

    @patch('info_pages.views.render_to_response')
    def test_should_render_template_to_response_with_registration_form(self, mock_render_to_response):
        response = non_logged_in_front_page_view(sentinel.request)
        self.assertCalledOnce(
            mock_render_to_response,
            'non_logged_in_front_page.html',
            {}
        )
        self.assertEquals(response, mock_render_to_response.return_value)



class TestInfoPageView(ResolverTestCase):

    @patch('info_pages.views.render_to_response')
    def test_should_render_template_to_response_with_user(self, mock_render_to_response):
        request = Mock()
        request.user.is_authenticated.return_value = False
        response = info_page_view(request, "my_template_name")
        self.assertCalledOnce(
            mock_render_to_response,
            'my_template_name.html',
            {
                'user': request.user
            }
        )
        self.assertEquals(response, mock_render_to_response.return_value)
