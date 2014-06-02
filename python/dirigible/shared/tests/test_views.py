# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from django.http import HttpRequest, HttpResponsePermanentRedirect

from dirigible.shared.views import redirect_to


class TestRedirectTo(unittest.TestCase):

    def test_redirect_to_no_params(self):
        request = HttpRequest()
        url = "http://blog.projectdirigible.com/"
        response = redirect_to(request, url)
        self.assertTrue(isinstance(response, HttpResponsePermanentRedirect))
        self.assertEquals(response.status_code, 301)
        self.assertEquals(response['Location'], url)


    def test_redirect_to_with_params(self):
        request = HttpRequest()
        request.META["QUERY_STRING"] = 'feed=rss2'
        url = "http://blog.projectdirigible.com/"
        response = redirect_to(request, url)
        self.assertTrue(isinstance(response, HttpResponsePermanentRedirect))
        self.assertEquals(response.status_code, 301)
        self.assertEquals(response['Location'], url + '?feed=rss2')
