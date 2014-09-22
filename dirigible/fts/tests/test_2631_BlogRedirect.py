# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from urllib2 import urlopen
from urlparse import urljoin


from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT, Url


# This test is a bit of a pain.  Ideally we'd visit the blog URLs in Selenium and
# check that get_location() returned the correct redirected-to URLs.  The problem
# is that when Selenium is driving Chrome, and it visits a page on our tested
# domain that redirects to another domain, Chrome blows up because it suspects
# some kind of cross-site scripting attack.  This is a specific instance of the
# more general problem that a Selenium test driving Chrome can access one and only
# one domain.
#
# As a result, we can't use Selenium, so this test doesn't actually run in a
# browser.
class Test_2631_BlogRedirect(unittest.TestCase):

    def test_blog_page_redirect(self):
        # Harold has a bookmark to our blog, but it dates from a long time ago when
        # it was hosted at projectdirigible.com/blog.  He visits it.
        old_blog_url = urljoin(Url.ROOT, '/blog/')
        opened_page = urlopen(old_blog_url)

        # He finds himself at blog.projectdirigible.com.
        self.assertEquals(opened_page.geturl(), "http://blog.projectdirigible.com/")

        # He goes to a specific post that he bookmarked because he found it interesting
        opened_page = urlopen(urljoin(old_blog_url, "?p=196"))

        # He finds himself on the equivalent page on the new site.
        self.assertEquals(opened_page.geturl(), "http://blog.projectdirigible.com/?p=196")


    def test_blog_rss_redirect(self):
        # Harold subscribed to our blog's RSS feed a long time ago when it was hosted
        # at projectdirigible.com/blog.  His RSS reader tries to access the feed.
        old_rss_url = urljoin(Url.ROOT, '/blog/?feed=rss2')
        opened_page = urlopen(old_rss_url)

        # It winds up getting it from blog.projectdirigible.com.
        self.assertEquals(opened_page.geturl(), "http://blog.projectdirigible.com/?feed=rss2")