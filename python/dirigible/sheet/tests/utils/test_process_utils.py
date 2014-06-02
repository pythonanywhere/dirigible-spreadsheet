# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import re
import stat
from subprocess import call as subprocess_call
import tempfile
from textwrap import dedent

from mock import Mock, patch, sentinel

from dirigible.test_utils import ResolverTestCase

from dirigible.sheet.cell import undefined
from dirigible.sheet.worksheet import Worksheet, worksheet_from_json, worksheet_to_json
from dirigible.sheet.utils.process_utils import (
    CHROOT_REQUIRED_MOUNTS, chroot_jail, create_chroot_jail,
    destroy_chroot_jail, chroot_calculate
)


class TestChrootJails(ResolverTestCase):

    REQUIRED_DIRS = ["dev", "etc", "lib", "usr"]

    @patch('dirigible.sheet.utils.process_utils.subprocess.call')
    @patch('dirigible.sheet.utils.process_utils.mkdtemp')
    def test_create_chroot_jail_does(self, mock_mkdtemp, mock_call):
        check_files = ['random', 'resolv.conf', 'libc.so.6', 'lib']

        temp_dir = tempfile.mkdtemp()

        e = None
        try:
            def mock_mkdtemp_side_effect(dir=None):
                self.assertIsNone(dir)
                return temp_dir
            mock_mkdtemp.side_effect = mock_mkdtemp_side_effect

            def mock_call_side_effect(args):
                self.assertEqual(args[0], 'sudo')
                subprocess_call(args)
            mock_call.side_effect = mock_call_side_effect

            jail_dir = create_chroot_jail()

            self.assertEqual(jail_dir, temp_dir)
            mode = os.stat(temp_dir).st_mode
            self.assertTrue(stat.S_ISDIR(mode))
            self.assertEqual(stat.S_IMODE(mode),
                                    stat.S_IRUSR |
                                    stat.S_IWUSR |
                                    stat.S_IXUSR |
                                    stat.S_IRGRP |
                                    stat.S_IXGRP |
                                    stat.S_IROTH |
                                    stat.S_IXOTH)


            self.assertEqual(set(os.listdir(temp_dir)), set(self.REQUIRED_DIRS))

            for check_file, dir in zip(check_files, self.REQUIRED_DIRS):
                self.assertTrue(check_file in os.listdir(os.path.join(temp_dir, dir)),
                                'File %r not found in %r' % (check_file, dir))

            real_resolv_conf = open('/etc/resolv.conf')
            real_resolv_conf_contents = real_resolv_conf.read()
            real_resolv_conf.close()

            copy_resolv_conf = open(os.path.join(jail_dir, 'etc', 'resolv.conf'))
            copy_resolv_conf_contents = copy_resolv_conf.read()
            copy_resolv_conf.close()

            random_stat = os.stat(os.path.join(jail_dir, 'dev', 'random'))
            self.assertEquals(random_stat.st_rdev, 264)

            urandom_stat = os.stat(os.path.join(jail_dir, 'dev', 'urandom'))
            self.assertEquals(urandom_stat.st_rdev, 265)

            self.assertEquals(real_resolv_conf_contents, copy_resolv_conf_contents)

        except Exception, e:
            raise
        finally:
            try:
                for dir in CHROOT_REQUIRED_MOUNTS:
                    target_dir = os.path.join(temp_dir, dir[1:])
                    subprocess_call(["umount", target_dir])
                    os.removedirs(target_dir)
            except:
                pass
            if e:
                raise


    @patch('dirigible.sheet.utils.process_utils.subprocess.call')
    @patch('dirigible.sheet.utils.process_utils.shutil.rmtree')
    def test_destroy_chroot_jail(self, mock_rmtree, mock_call):
        jail_dir = '/tmp/my_jail'
        def test_mountpoints_cleared(dir, ignore_errors):
            call_args = [
                ((['sudo', 'umount', "-l", os.path.join(jail_dir, required_dir[1:])],), {})
                for required_dir in CHROOT_REQUIRED_MOUNTS
            ]
            self.assertEquals(mock_call.call_args_list, call_args)
        mock_rmtree.side_effect = test_mountpoints_cleared
        destroy_chroot_jail(jail_dir)
        mock_rmtree.assert_called_with(jail_dir, ignore_errors=True)


    def test_destroy_chroot_jail_on_missing_dir(self):
        try:
            destroy_chroot_jail('/tmp/no_such_place')
        except OSError:
            self.fail('destroy_chroot_jail falls over if the specified directory is missing')


    @patch('dirigible.sheet.utils.process_utils.pexpect')
    @patch('dirigible.sheet.utils.process_utils.xmlrpclib')
    @patch('dirigible.sheet.utils.process_utils.create_chroot_jail')
    @patch('dirigible.sheet.utils.process_utils.destroy_chroot_jail')
    def test_chroot_calculate_creates_chroot_jail_starts_and_calls_server_destroys_jail_and_returns_results(
        self, mock_destroy_jail, mock_create_jail, mock_xmlrpclib, mock_pexpect
    ):
        process = mock_pexpect.spawn.return_value
        original_sheet_contents_json = sentinel.contents_json

        proxy = mock_xmlrpclib.ServerProxy.return_value

        def check_calculate_already_called(jail_dir):
            # Call proxy with JSON contents, and usercode and timeout
            self.assertCalledOnce(
                proxy.rpc_calculate,
                original_sheet_contents_json, sentinel.usercode,
                sentinel.timeout_seconds, sentinel.session_id
            )
        mock_destroy_jail.side_effect = check_calculate_already_called

        result = chroot_calculate(
            original_sheet_contents_json, sentinel.usercode,
            sentinel.timeout_seconds, sentinel.session_id
        )

        self.assertEquals(
            mock_create_jail.call_args_list,
            [((), {})]
        )

        # Start server
        server_script = '/home/dirigible/python/dirigible/sheet/calculate_server.py'
        python_root = '/home/dirigible/python'
        self.assertEquals(
            mock_pexpect.spawn.call_args_list,
            [(("sudo" , ["python", server_script, python_root, mock_create_jail.return_value],), {} )]
        )

        # Get port number
        self.assertEquals(
            process.expect.call_args_list,
            [((re.compile(r'Listening on port ([0-9]+)'),), {})]
            )
        self.assertEquals(
            process.match.group.call_args_list,
            [((1,), {})]
            )
        port_number = process.match.group.return_value

        # Create proxy attached to port
        server_url = "http://localhost:%s/" % (port_number,)
        self.assertEquals(
            mock_xmlrpclib.ServerProxy.call_args_list,
            [((server_url,), {})]
            )

        mock_destroy_jail.assert_called_with(mock_create_jail.return_value)

        # Return proxy call's return value
        self.assertEquals(result, proxy.rpc_calculate.return_value)


    @patch('dirigible.sheet.utils.process_utils.xmlrpclib', Mock())
    @patch('dirigible.sheet.utils.process_utils.pexpect')
    def test_chroot_calculate_disposes_of_process_on_exception(self, mock_pexpect):
        mock_process = Mock()
        mock_pexpect.spawn.return_value = mock_process
        def die(_):
            raise ZeroDivisionError()
        mock_process.expect = die

        with self.assertRaises(ZeroDivisionError):
            chroot_calculate(None, None, None, None)

        self.assertTrue(mock_process.close.called)


class TestChrootJailDecorator(unittest.TestCase):

    @patch('dirigible.sheet.utils.process_utils.create_chroot_jail')
    @patch('dirigible.sheet.utils.process_utils.destroy_chroot_jail')
    def test_chroot_jail_decorator(self, mock_destroy, mock_create):
        self.decorated_func_called = False

        @chroot_jail
        def decorated_fn(jail_dir):
            self.decorated_func_called = True
            self.assertTrue(mock_create.called)
            self.assertFalse(mock_destroy.called)
            return 1234

        result = decorated_fn()

        self.assertTrue(self.decorated_func_called)
        self.assertEquals(result, 1234)
        self.assertTrue(mock_destroy.called)


    @patch('dirigible.sheet.utils.process_utils.create_chroot_jail')
    @patch('dirigible.sheet.utils.process_utils.destroy_chroot_jail')
    def test_chroot_jail_decorator_handles_exceptions(
        self, mock_destroy, mock_create
    ):
        self.decorated_func_called = False
        self.assertFalse(mock_destroy.called)

        @chroot_jail
        def decorated_fn(jail_dir):
            raise ZeroDivisionError('ohlookout!')

        with self.assertRaises(ZeroDivisionError):
            decorated_fn()

        self.assertTrue(mock_destroy.called)



class TestChrootCalculateBasicSemiFunctional(unittest.TestCase):

    def test_simple_formula(self):
        worksheet_before = Worksheet()
        worksheet_before.A1.formula = "1"
        worksheet_before.A2.formula = "2"
        worksheet_before.A3.formula = "=a1+a2"
        usercode = dedent("""
            load_constants(worksheet)
            evaluate_formulae(worksheet)
        """)
        calculated_json = chroot_calculate(
            worksheet_to_json(worksheet_before), usercode,
            1, 'session_id'
        )
        worksheet_after = worksheet_from_json(calculated_json)
        self.assertIsNone(worksheet_after._usercode_error)
        self.assertEquals(worksheet_after.A1.value, 1)
        self.assertEquals(worksheet_after.A2.value, 2)
        self.assertEquals(worksheet_after.A3.value, 3)


    def test_simple_formula_error(self):
        worksheet_before = Worksheet()
        worksheet_before.A1.formula = "=1/0"
        worksheet_before.A2.formula = "2"
        usercode = dedent("""
            load_constants(worksheet)
            evaluate_formulae(worksheet)
        """)
        calculated_json = chroot_calculate(
            worksheet_to_json(worksheet_before), usercode,
            1, 'session_id'
        )
        worksheet_after = worksheet_from_json(calculated_json)
        self.assertIsNone(worksheet_after._usercode_error)
        self.assertEquals(worksheet_after.A1.value, undefined)
        self.assertEquals(worksheet_after.A1.error, "ZeroDivisionError: float division")
        self.assertEquals(worksheet_after.A2.value, 2)


    def test_simple_usercode(self):
        worksheet_before = Worksheet()
        usercode = "worksheet.A1.value = 23"
        calculated_json = chroot_calculate(
            worksheet_to_json(worksheet_before), usercode,
            1, 'session_id'
        )
        worksheet_after = worksheet_from_json(calculated_json)
        self.assertIsNone(worksheet_after._usercode_error)
        self.assertEquals(worksheet_after.A1.value, 23)


    def test_simple_usercode_error(self):
        worksheet_before = Worksheet()
        usercode = "wibble"
        calculated_json = chroot_calculate(
            worksheet_to_json(worksheet_before), usercode,
            1, 'session_id'
        )
        worksheet_after = worksheet_from_json(calculated_json)
        self.assertIsNotNone(worksheet_after._usercode_error)
        self.assertTrue("NameError: name 'wibble' is not defined" in worksheet_after._usercode_error['message'],
                        'user_code error was %r' % (worksheet_after._usercode_error,))
        self.assertEquals(worksheet_after.A1.value, undefined)



class TestChrootCalculateSecuritySemiFunctional(unittest.TestCase):

    def test_dirigible_settings_not_importable(self):
        calculated_json = chroot_calculate(
            worksheet_to_json(Worksheet()), 'import dirigible.settings',
            1, 'session_id'
        )
        worksheet = worksheet_from_json(calculated_json)
        self.assertIsNotNone(worksheet._usercode_error, "where's my error?")
        self.assertTrue('ImportError: No module named settings' in worksheet._usercode_error['message'],
                        'user_code error was %r' % (worksheet._usercode_error,))


    def test_dirigible_users_not_importable(self):
        calculated_json = chroot_calculate(
            worksheet_to_json(Worksheet()),
            'from dirigible.sheet.models import User',
            1, 'session_id'
        )
        worksheet = worksheet_from_json(calculated_json)
        self.assertIsNotNone(worksheet._usercode_error, "where's my error?")
        self.assertTrue('ImportError: No module named models' in worksheet._usercode_error['message'],
                        'user_code error was %r' % (worksheet._usercode_error,))

