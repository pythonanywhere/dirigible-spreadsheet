# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, sentinel
import pwd

from dirigible.sheet.calculate_server import main, rpc_calculate, run


class TestCalculateServer(unittest.TestCase):

    @patch('dirigible.sheet.calculate_server.calculate_with_timeout')
    @patch('dirigible.sheet.calculate_server.worksheet_from_json')
    @patch('dirigible.sheet.calculate_server.worksheet_to_json')
    def test_calculate_should_call_calculate_with_timeout_with_unjsonified_worksheet_usercode_and_timeout_and_return_worksheet_json(
        self, mock_worksheet_to_json, mock_worksheet_from_json, mock_calculate_with_timeout
    ):
        def check_calculate_with_timeout_has_been_called(*_):
            self.assertTrue(mock_calculate_with_timeout.called)
            return mock_worksheet_to_json.return_value
        mock_worksheet_to_json.side_effect = check_calculate_with_timeout_has_been_called

        retval = rpc_calculate(
            sentinel.worksheet_json, sentinel.usercode,
            sentinel.timeout, sentinel.session_id
        )

        self.assertEquals(
            mock_worksheet_from_json.call_args_list,
            [((sentinel.worksheet_json,), {})]
        )
        self.assertEquals(
            mock_calculate_with_timeout.call_args_list,
            [((mock_worksheet_from_json.return_value, sentinel.usercode, sentinel.timeout, sentinel.session_id), {})]
        )

        self.assertEquals(
            mock_worksheet_to_json.call_args_list,
            [((mock_worksheet_from_json.return_value,), {})]
        )
        self.assertEquals(retval, mock_worksheet_to_json.return_value)


    @patch('dirigible.sheet.calculate_server.os')
    @patch('dirigible.sheet.calculate_server.SimpleXMLRPCServer')
    @patch('dirigible.sheet.calculate_server.sys.stdout')
    def test_run_exposes_calc_function_by_rpc_server_in_a_chroot_jail_on_a_free_port_which_it_prints(
        self, mock_stdout, mock_rpcserver, mock_os
    ):
        server = mock_rpcserver.return_value
        server.socket.getsockname.return_value = \
            (sentinel.addr, sentinel.port_number)

        def check_server_handles_requests_from_chroot_jail():
            mock_os.chroot.assert_called_with(sentinel.chroot_jail_path)
            mock_os.chdir.assert_called_with('/')
            mock_os.seteuid.assert_called_with(pwd.getpwnam("nobody").pw_uid)
        server.handle_request.side_effect = check_server_handles_requests_from_chroot_jail

        run(sentinel.chroot_jail_path)

        self.assertEquals(
            mock_rpcserver.call_args_list,
            [((('localhost', 0),), {})]
        )
        expected_output = 'Listening on port %s' % (sentinel.port_number,)
        self.assertEquals(
            mock_stdout.write.call_args_list,
            [
                ((expected_output,), {}),
                (('\n',), {}),
            ]
        )
        self.assertEquals(
            server.register_function.call_args_list,
            [((rpc_calculate, 'rpc_calculate'), {})]
        )

        self.assertTrue(server.handle_request.called)


    @patch('dirigible.sheet.calculate_server.run')
    @patch('dirigible.sheet.calculate_server.sys')
    def test_calculate_server_main_adds_first_arg_to_sys_path_and_calls_run_with_second(self, mock_sys, mock_run):
        mock_sys.path = ['/path/to/dirigible', 'elsewhere']
        mock_sys.argv = ['', 'sentinel.python_root', sentinel.chroot_jail_path]
        main()
        self.assertEquals(mock_sys.path, ['elsewhere', 'sentinel.python_root'])
        mock_run.assert_called_with(sentinel.chroot_jail_path)
