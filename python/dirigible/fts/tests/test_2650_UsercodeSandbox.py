# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#
from textwrap import dedent

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from functionaltest import FunctionalTest


class Test_2650_UsercodeSandbox(FunctionalTest):

    def test_dirigible_package_is_off_limits(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He puts on his black hat and tries to access the sheets that
        #   belong to other users
        self.prepend_usercode('from dirigible.sheet.models import User')

        # * Dirigible notices his naughtiness and stops it
        self.wait_for_console_content(dedent('''
            ImportError: No module named models
                User code line 1''')[1:])


    def test_dirigible_settings_not_accessible(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He puts on his black hat and tries to access dirigible settings
        self.prepend_usercode('import dirigible.settings')

        # * Dirigible notices his naughtiness and stops it
        self.wait_for_console_content(dedent('''
            ImportError: No module named settings
                User code line 1''')[1:])


    def test_sys_path_omits_dirigible_dirs(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He notes that sys.path does not contain any dirigible directories
        self.append_usercode(dedent('''
            import sys
            worksheet[1, 1].value = False
            for path in sys.path:
                if 'dirigible' in path:
                    worksheet[1, 1].value = True
            worksheet[1, 2].value = 'done'
        '''))

        self.wait_for_cell_value(1, 2, 'done')
        self.assertEquals(
            self.get_cell_text(1, 1), 'False',
            'there was a dirigible directory in sys.path')


    def test_harold_looks_at_his_root_directory(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He sees a limited subset of the filesystem
        self.append_usercode(dedent('''
            import os
            worksheet[1, 1].value = sorted(os.listdir("/"))
        ''')[1:])
        self.wait_for_cell_value(1, 1, "['dev', 'etc', 'lib', 'usr']")


    def test_harold_tries_to_create_a_file_in_cwd(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He tries to create a file in the current dir
        self.prepend_usercode(dedent('''
            import os
            os.mknod('foo.txt')
        ''')[1:])

        # * Dirigible notices his naughtiness and stops it
        self.wait_for_console_content(dedent('''
            OSError: [Errno 13] Permission denied
                User code line 2''')[1:])


    def test_harold_tries_to_create_a_file_in_usr(self):
        # * Harold logs in and creates a new sheet
        self.login_and_create_new_sheet()

        # * He tries to create a file in the current dir
        self.prepend_usercode(dedent('''
            import os
            os.mknod('/usr/lib/foo.txt')
        ''')[1:])

        # * Dirigible notices his naughtiness and stops it
        self.wait_for_console_content(dedent('''
            OSError: [Errno 13] Permission denied
                User code line 2''')[1:])

