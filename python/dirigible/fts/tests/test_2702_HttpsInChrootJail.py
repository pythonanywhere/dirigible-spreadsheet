# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest


class Test_2702_HttpsInChrootJail(FunctionalTest):

    def test_numpy_tutorial_create_arrays(self):
        # * Harold wants to access https URLs from his Dirigible sheets
        # * He logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * .. and adds a get for a https URL in an S3 bucket
        self.prepend_usercode(dedent('''
            from urllib2 import urlopen
            connection = urlopen('https://s3.amazonaws.com/oecd-data/oecd-data.csv')
            content = connection.read()
            worksheet.A1.value = 'Canada' in content
        '''))

        # * and notes that he gets the expected content
        self.wait_for_cell_value(1, 1, 'True')


