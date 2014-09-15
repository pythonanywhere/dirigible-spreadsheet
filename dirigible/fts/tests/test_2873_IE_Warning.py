# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from functionaltest import FunctionalTest

class Test_2873_IE_Warning(FunctionalTest):

    def test_IE_warnings(self):
        should_warning_be_visible = 'iexplore' in self.selenium.browserStartCommand

        # Harold goes to the Dirigible home page
        self.go_to_url('/')

        # No warning here, either way...
        self.wait_for_element_presence('id=id_ie_warning', False)

        # He clicks on the signup link
        self.click_link("id_signup_link")

        # If he's using IE, he spots a warning sign telling him he ain't
        # weclome round these parts. If he isn't, he doesn't.
        self.wait_for_element_presence('id=id_ie_warning', should_warning_be_visible)

        # * He then logs in and goes to a new sheet
        self.login_and_create_new_sheet()

        # If he's using IE, he spots a warning sign telling him he ain't
        # weclome round these parts. If he isn't, he doesn't.
        self.wait_for_element_presence('id=id_ie_warning', should_warning_be_visible)

        # He goes back to his account page and sees a warning there too
        self.go_to_url('/')
        self.wait_for_element_presence('id=id_ie_warning', should_warning_be_visible)



