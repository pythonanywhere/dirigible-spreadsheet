# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from urlparse import urljoin

from functionaltest import FunctionalTest, PAGE_LOAD_TIMEOUT, Url


class Test_2544_404And500Pages(FunctionalTest):

    user_count = 2


    def test_403(self):
        harriet = self.get_my_usernames()[1]
        self.login_and_create_new_sheet(harriet)
        sheet_url = self.browser.current_url
        self.logout()

        # * Harold goes to a page he should not have access to
        harold = self.get_my_username()
        self.login(harold)
        ## Older versions of Selenium (like the one we use for IE) signal errors
        ## with exceptions.  Newer ones don't.  We handle the former case by
        ## looking at the exception details; for the latter we rely on the checks
        ## of the page text below.
        try:
            self.selenium.open(sheet_url)
        except Exception, e:
            self.assertTrue("403" in str(e), "Error not a 403: %s" % (e,))

        # * He gets an appropriate Dirigible-specific 403 page.
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.check_page_load(sheet_url)
        self.assertEquals(self.selenium.get_title(), "Access Forbidden: Dirigible")
        self.assertEquals(self.selenium.get_text("id=id_server_error_title"), "403 Access Forbidden")
        error_text = self.selenium.get_text("id=id_server_error_text")
        self.assertTrue("This page is private and belongs to someone else." in error_text)

        # There is also a link to the Dirigible home page, which he follows and discovers
        # that it works.
        self.click_link('id_link_home')
        self.assertEquals(self.browser.current_url, Url.ROOT)



    def test_404(self):
        # * Harold goes to a non-existent page
        url = urljoin(Url.ROOT, '/notaVALIDpage/')
        ## Older versions of Selenium (like the one we use for IE) signal errors
        ## with exceptions.  Newer ones don't.  We handle the former case by
        ## looking at the exception details; for the latter we rely on the checks
        ## of the page text below.
        try:
            self.selenium.open(url)
        except Exception, e:
            self.assertTrue("404" in str(e), "Error not a 404: %s" % (e,))

        # * He gets an appropriate Dirigible-specific 404 page.
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.check_page_load(url)
        self.assertEquals(self.selenium.get_title(), "Page not found: Dirigible")
        self.assertEquals(self.selenium.get_text("id=id_server_error_title"), "404 Not Found")
        error_text = self.selenium.get_text("id=id_server_error_text")
        self.assertTrue("The page that you seek" in error_text)
        self.assertTrue("can't be found; lost in the clouds." in error_text)
        self.assertTrue("Please look somewhere else" in error_text)

        # There is a link to the Dirigible home page, which he follows and discovers
        # that it works.
        self.click_link('id_link_home')
        self.assertEquals(self.browser.current_url, Url.ROOT)



    def test_500(self):
        # * Harold somehow triggers an internal server error
        self.login_and_create_new_sheet()
        url = urljoin(self.browser.current_url, 'set_cell_formula/')
        ## Older versions of Selenium (like the one we use for IE) signal errors
        ## with exceptions.  Newer ones don't.  We handle the former case by
        ## looking at the exception details; for the latter we rely on the checks
        ## of the page text below.
        try:
            self.selenium.open(url)
        except Exception, e:
            self.assertTrue("500" in str(e), "Error not a 500: %s" % (e,))

        # * He gets an appropriate Dirigible-specific 500 page.
        self.selenium.wait_for_page_to_load(PAGE_LOAD_TIMEOUT)
        self.check_page_load(url)
        self.assertEquals(self.selenium.get_title(), "Server error: Dirigible")
        self.assertEquals(self.selenium.get_text("id=id_server_error_title"), "500 Internal Server Error")
        error_text = self.selenium.get_text("id=id_server_error_text")
        self.assertTrue("Sorry, something has gone wrong!" in error_text)
        self.assertTrue("The Dirigible team have notified and will look into the problem ASAP." in error_text)

        # There is a link to the Dirigible home page, which he follows and discovers
        # that it works.
        self.click_link('id_link_home')
        self.assertEquals(self.browser.current_url, Url.ROOT)
