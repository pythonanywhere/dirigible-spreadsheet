# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from mock import patch
from textwrap import dedent

from django.http import HttpRequest, HttpResponse

from dirigible.settings import FEEDBACK_EMAIL, SERVER_EMAIL
from dirigible.test_utils import ResolverTestCase

from dirigible.feedback.views import submit


class SubmitTest(ResolverTestCase):

    @patch('dirigible.feedback.views.send_mail')
    def test_submit_with_message_and_email_address_and_username_sends_admin_email_with_all_three(self, mock_send_mail):
        request = HttpRequest()
        request.POST["message"] = "a test message"
        request.POST["email_address"] = "a test email address"
        request.POST["username"] = "a test username"
        request.META['HTTP_REFERER'] = 'a test page'

        response = submit(request)

        self.assertTrue(isinstance(response, HttpResponse))
        self.assertEquals(response.content, "OK")

        self.assertCalledOnce(
            mock_send_mail,
            "User feedback from Dirigible",
            dedent("""
                Username: a test username
                Email address: a test email address
                Page: a test page

                Message:
                a test message
            """),
            SERVER_EMAIL,
            [FEEDBACK_EMAIL]
        )
