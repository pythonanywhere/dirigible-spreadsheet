# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest


class Test_2701_NameResolutionWorks(FunctionalTest):

    def test_name_resolution(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # * He writes some usercode that does something to test
        #   name resolution.
        self.enter_usercode(dedent("""
            from urllib2 import urlopen, URLError
            try:
                connection = urlopen("http://www.google.com/")
                worksheet[1, 1].value = len(connection.read())
                connection.close()
            except URLError, e:
                worksheet[1, 1].value = e.reason[1]
            except Exception, e:
                worksheet[1, 1].value = str(e)
        """))

        # * It runs OK.
        self.wait_for_spinner_to_stop()
        size = int(self.get_cell_text(1, 1))
        self.assertTrue(size > 0)
