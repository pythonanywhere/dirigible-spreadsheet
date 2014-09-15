# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from urlparse import urljoin


from functionaltest import FunctionalTest, Url


class Test_2571_Documentation(FunctionalTest):

    def get_link_href(self, link_id):
        url = self.selenium.get_attribute("id=%s@href" % (link_id,))
        return urljoin(Url.ROOT, url)


    def test_main_documentation_page_exists(self):
        # * Harold goes to the Dirigible front page.
        self.go_to_url(Url.ROOT)

        # * He sees that there is a link to a blog, and notes down where it goes to.
        blog_url = self.get_link_href("id_blog_link")

        # * He goes to url http://IP/documentation
        self.go_to_url(Url.DOCUMENTATION)

        # * He gets back a page, not a 404, the title of which which contains the words 'Dirigible' and 'documentation'
        title = self.browser.title.lower()
        self.assertTrue("documentation" in title)
        self.assertTrue("dirigible" in title)

        # * He logs in and creates a sheet, and notices that there is a link to the
        #   same documentation page.
        self.login_and_create_new_sheet()
        self.assertEquals(self.get_link_href("id_help_link"), Url.DOCUMENTATION)

        # ...and that there is also a link to the same blog.
        self.assertEquals(self.get_link_href("id_blog_link"), blog_url)

        # * He follows the link to his dashboard.
        self.click_link('id_account_link')

        # * He sees the same help and blog links there, and confirms they go to the same places.
        self.assertEquals(self.get_link_href("id_help_link"), Url.DOCUMENTATION)
        self.assertEquals(self.get_link_href("id_blog_link"), blog_url)