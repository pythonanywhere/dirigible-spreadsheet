# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from urlparse import urlparse, urlunparse

from functionaltest import FunctionalTest


class Test_2616_RootPageIsDashboard(FunctionalTest):

    # The bulk of this was tested by changing the existing functional tests to reflect the new
    # behaviour; we just have new stuff in this file.

    def test_old_url_redirects(self):
        # Harold has some old bookmarks to pages that have moved as part of this story.
        # He is delighted to find they still work.
        self.assert_redirects('/static/dirigible/about.html', '/about/')
        self.assert_redirects('/static/dirigible/contact.html', '/contact/')
        self.assert_redirects('/static/dirigible/pricing.html', '/pricing/')
        self.assert_redirects('/static/dirigible/privacy.html', '/privacy/')
        self.assert_redirects('/static/dirigible/terms.html', '/terms/')
        self.assert_redirects('/static/dirigible/video.html', '/video/')
