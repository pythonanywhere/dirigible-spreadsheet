# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

from textwrap import dedent

from functionaltest import FunctionalTest


class test_2751_UsefulModules(FunctionalTest):

    def test_can_import_useful_modules(self):
        # * Harold logs in to Dirigible and creates a new sheet
        self.login_and_create_new_sheet()

        # He writes some usercode that imports a bunch of modules
        # and then sets a cell to a value to prove that it worked.
        self.prepend_usercode(dedent("""
            ## pycrypto
            from Crypto.Hash import MD5
            ## sqlalchemy
            from sqlalchemy import *
            ## lxml
            from lxml import *
            ## rdflib
            from rdflib.graph import Graph
            ## geopy
            from geopy import *
            ## BeautifulSoup
            from BeautifulSoup import *
            ## mechanize
            from mechanize import *

            worksheet.A1.value = 21
        """))

        # The cell has the right value
        self.wait_for_cell_value(1, 1, "21")