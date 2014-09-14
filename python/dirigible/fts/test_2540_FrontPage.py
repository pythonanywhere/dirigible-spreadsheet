# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#


from functionaltest import FunctionalTest, Url

from browser_settings import SERVER_IP


import urllib2
import urlparse

class Test_2540_FrontPage(FunctionalTest):

    def check_url_not_broken(self, url):
        try:
            response = urllib2.urlopen(url)
        except Exception, e:
            self.fail("Error getting url %s: %s" % (url, str(e)))


    def check_links_not_broken_for_tag_attribute(self, tag_xpath, attribute):
        num_tags = self.selenium.get_xpath_count(tag_xpath)
        base_file_location = self.selenium.get_location()
        for i in range(1, num_tags + 1):
            src = self.selenium.get_attribute("xpath=(%s)[%s]@%s" % (tag_xpath, i, attribute))
            url = urlparse.urljoin(base_file_location, src)
            if not url.startswith("mailto:"):
                self.check_url_not_broken(url)


    def test_front_page_links(self):
        # Harold goes to Dirigible's root page
        self.go_to_url('http://%s/' % (SERVER_IP,))

        # He finds a page with the title  "Welcome to Dirigible"
        self.assertEquals(self.selenium.get_title(), 'Welcome to Dirigible')

        # The CSS files are all loaded correctly
        self.check_links_not_broken_for_tag_attribute("//link[@rel='stylesheet']", "href")

        # As are the images
        self.check_links_not_broken_for_tag_attribute("//img", "src")

        # And the links
        self.check_links_not_broken_for_tag_attribute("//a", "href")

        # He notes in particular that the "log in" link take him to the login page.
        front_page = self.selenium.get_location()
        login_url = self.selenium.get_attribute("xpath=//a[text() = 'Log in']@href")
        self.assert_sends_to_login_page(login_url)
        self.go_to_url(front_page)

        # ...and that the "Pricing", "Find out more", "Watch a video", "Help", "Terms & Conditions",
        # "Privacy Policy", and "Contact Us" take him to pages which have appropriate-looking titles.
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[@id='id_pricing_link']@href"),
            'Dirigible Pricing'
        )
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[img[@id='id_find_out_more']]@href"),
            'About Dirigible'
        )
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[img[@id='id_watch_a_video']]@href"),
            'The Video: Dirigible'
        )
        self.assert_page_title_contains(
            self.selenium.get_attribute("xpath=//a[text() = 'Help']@href"),
            'Dirigible documentation'
        )
        self.assert_has_useful_information_links()