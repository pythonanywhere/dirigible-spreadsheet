# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

from datetime import datetime
from Queue import Queue
import sys
from textwrap import dedent
from unittest import SkipTest
from urllib import urlencode


from mock import call, Mock, patch, sentinel

from dirigible.test_utils import die, ResolverTestCase

import sheet.calculate as calculate_module
from sheet.calculate import (
    api_json_to_worksheet, calculate, calculate_with_timeout,
    create_cell_recalculator, CURRENT_API_VERSION, evaluate_formulae_in_context,
    execute_usercode, format_traceback, is_nan, load_constants, _raise, recalculate_cell,
    run_worksheet, MyStdout)
from sheet.cell import Cell, undefined
from sheet.dirigible_datetime import DateTime
from sheet.models import Sheet, User
from sheet.parser import FormulaError
from sheet.views_api_0_1 import _sheet_to_value_only_json
from sheet.worksheet import CellRange, Worksheet, worksheet_from_json, worksheet_to_json



class TestIsNan(ResolverTestCase):

    def test_is_nan(self):
        self.assertTrue(is_nan(float('nan')))
        self.assertFalse(is_nan(23.3))
        self.assertFalse(is_nan(23))

    def test_is_nan_with_numpy(self):
        # known to cause problems historically:
        try:
            import numpy
            self.assertFalse(is_nan(numpy.array([1, 2, 3])))
        except ImportError:
            raise SkipTest('No numpy')



class TestLoadConstants(ResolverTestCase):

    @patch('sheet.calculate.eval_constant')
    def test_load_constants_should_call_eval_constant_only_on_every_constant_location(self, mock_eval_constant):
        worksheet = Worksheet()
        worksheet[11,1].formula = "=formula1"
        worksheet[22,2].formula = "constant"
        worksheet[33,3].formula = "=formula2"
        worksheet[44,4].formula = "another constant"

        load_constants(worksheet)
        expected = [
            (("constant",), {}),
            (("another constant",), {}),
        ]
        self.assertItemsEqual(mock_eval_constant.call_args_list, expected)


    def test_load_constants_should_clear_errors_for_constants(self):
        cell = Cell()
        cell.formula = "a constant"
        cell.error = 'Ohno!'
        worksheet = Worksheet()
        worksheet.A1 = cell

        load_constants(worksheet)

        self.assertIsNone(cell.error)



class TestRecalculateCell(ResolverTestCase):

    def test_recalculate_cell_evals_python_formula_in_context_and_puts_results_in_worksheet(self):
        location = (1, 2)
        cell = Cell()
        cell.python_formula = '100 + fred'
        context = { 'fred': 23, "worksheet": { location: cell } }

        # Mocked out to avoid explosion -- tested in another unit test.
        node = Mock()
        node.parents = []

        recalculate_cell(location, None, { location: node }, context)

        self.assertEquals(cell.value, 123)


    def test_recalculate_cell_should_perform_true_division(self):
        location = (1, 2)
        cell = Cell()
        cell.python_formula = '1/4'
        context = { "worksheet": { location: cell } }

        # Mocked out to avoid explosion -- tested in another unit test.
        node = Mock()
        node.parents = []

        recalculate_cell(location, None, { location: node }, context)

        self.assertEquals(cell.value, 0.25)


    def test_recalculate_cell_should_remove_nodes_from_dependency_graph(self):
        location = (1, 2)
        cell = Cell()
        cell.formula = '=123'
        leaf_queue = Queue()
        parent = Mock()
        parent_loc = (2, 3)
        node = Mock()
        node.parents = set([(parent_loc)])
        graph = { location: node, parent_loc: parent }
        context = { 'worksheet': { location: cell, } }

        recalculate_cell(location, leaf_queue, graph, context)

        self.assertEquals( node.remove_from_parents.call_args, (([parent], leaf_queue,), {}) )


    def test_recalc_cell_catches_cell_errors_and_adds_them_to_console(self):
        cell = Cell()
        cell.formula = "=123"
        cell.python_formula = '_raise(Exception("OMGWTFBBQ"))'
        cell.error = 'old error, just hanging around...'
        worksheet = Worksheet()
        location = (1, 11)
        worksheet[location] = cell

        # Mocked out to avoid explosion -- tested in another unit test.
        node = Mock()
        node.parents = []
        graph = {location: node }

        context = { 'worksheet': worksheet, "_raise": _raise }
        worksheet.add_console_text = Mock()

        recalculate_cell(location, Mock(), graph, context)

        self.assertEqual(
            worksheet[location].error,
            'Exception: OMGWTFBBQ'
        )

        expected_error_text = "Exception: OMGWTFBBQ\n    Formula '%s' in A11\n" % (
                cell.formula)

        self.assertCalledOnce(worksheet.add_console_text, expected_error_text)

        self.assertEquals(worksheet[location].value, undefined)


    def test_recalc_cell_should_clear_cell_error_and_not_add_to_console_text_on_eval_succeeding(self):
        cell = Cell()
        cell.formula = '=123'
        cell.error = 'old error, just hanging around...'
        worksheet = Worksheet()
        location = (1, 11)
        worksheet[location] = cell

        node = Mock()
        node.parents = []
        graph = {location: node }

        context = { 'worksheet': { location: cell, } }

        recalculate_cell(location, Mock(), graph, context)

        self.assertEqual(
            worksheet[location].error,
            None
        )
        self.assertEqual(
            worksheet[location].value,
            123
        )
        self.assertEqual(
            worksheet._console_text, ''
        )


class TestCreateCellRecalculator(ResolverTestCase):

    @patch('sheet.calculate.recalculate_cell')
    def test_create_cell_recalculator_should(self, mock_recalculate):
        unrecalculated_queue = Queue()
        unrecalculated_queue.put(1)
        unrecalculated_queue.put(1)
        unrecalculated_queue.task_done = Mock()

        leaf_queue = Queue()
        leaf_queue.put(sentinel.one)
        leaf_queue.put(sentinel.two)
        leaf_queue.task_done = Mock()

        target = create_cell_recalculator(leaf_queue, unrecalculated_queue, sentinel.graph, sentinel.context)
        target()

        self.assertTrue(unrecalculated_queue.empty())
        self.assertEquals(
            unrecalculated_queue.task_done.call_args_list,
            [ ((), {}), ((), {}), ]
        )

        self.assertTrue(leaf_queue.empty())

        self.assertEquals(
            mock_recalculate.call_args_list,
            [
                ((sentinel.one, leaf_queue, sentinel.graph, sentinel.context), {}),
                ((sentinel.two, leaf_queue, sentinel.graph, sentinel.context), {})
            ]
        )

        self.assertEquals(
            leaf_queue.task_done.call_args_list,
            [ ((), {}), ((), {}), ]
        )

    @patch('sheet.calculate.recalculate_cell')
    def test_create_cell_recalculator_should_handle_exceptions_from_recalc_cell(self, mock_recalculate):
        mock_recalculate.side_effect = die()
        unrecalculated_queue = Queue()
        unrecalculated_queue.put(1)
        unrecalculated_queue.task_done = Mock()

        leaf_queue = Queue()
        leaf_queue.put(sentinel.one)
        leaf_queue.task_done = Mock()

        target = create_cell_recalculator(leaf_queue, unrecalculated_queue, sentinel.graph, sentinel.context)
        self.assertRaises(AssertionError, target)

        self.assertTrue(unrecalculated_queue.empty())
        self.assertCalledOnce(unrecalculated_queue.task_done)
        self.assertTrue(leaf_queue.empty())
        self.assertCalledOnce(mock_recalculate, sentinel.one, leaf_queue, sentinel.graph, sentinel.context)
        self.assertCalledOnce(leaf_queue.task_done)


class TestEvaluateFormulaeInContext(ResolverTestCase):

    @patch('sheet.calculate.NUM_THREADS', 2)
    @patch('sheet.calculate.build_dependency_graph')
    @patch('sheet.calculate.Thread')
    @patch('sheet.calculate.Queue')
    @patch('sheet.calculate.create_cell_recalculator')
    def test_evaluate_formulae_in_context_builds_dependency_graph_and_recalculates_it_on_threads(
        self, mock_create_cell_recalculator, mock_queue_class, mock_thread_class,
        mock_build_dependency_graph
    ):
        mock_thread = mock_thread_class.return_value
        mock_queue_class.side_effect = lambda: Mock()
        mock_create_cell_recalculator.return_value = sentinel.create_cell_recalculator
        graph = {
            (1, 1): set([(1, 2), (1, 3)]),
            (1, 3): set([(2, 2), (2, 3)]),
            (2, 2): set(),
            (1, 2): set(),
            (2, 3): set()
        }
        leaves = [(2, 2), (1, 2), (2, 3)]
        mock_build_dependency_graph.return_value = ( graph, leaves )

        evaluate_formulae_in_context(Mock(), Mock())

        arg_ids = [map(id, x[0]) for x in mock_create_cell_recalculator.call_args_list]
        self.assertEquals(arg_ids[0][0], arg_ids[1][0], 'leaf queues passed into threads not the same')
        self.assertEquals(arg_ids[0][1], arg_ids[1][1], 'completed queues passed into threads not the same')
        self.assertEquals(
            [args[0][2] for args in mock_create_cell_recalculator.call_args_list],
            [graph, graph]
        )
        mock_leaf_queue = mock_create_cell_recalculator.call_args_list[0][0][0]
        self.assertEquals(
            mock_leaf_queue.put.call_args_list,
            [
               ((leaves[0],), {}),
               ((leaves[1],), {}),
               ((leaves[2],), {})
            ])

        unrecalculated_cell_queue = mock_create_cell_recalculator.call_args_list[0][0][1]
        self.assertEquals(len(unrecalculated_cell_queue.put.call_args_list), len(graph), 'unrecalculated queue not correctly populated')

        self.assertEquals(mock_thread_class.call_args_list,
            [
                ((), {'target': sentinel.create_cell_recalculator}),
                ((), {'target': sentinel.create_cell_recalculator}),
            ]
        )

        self.assertEquals(mock_thread.setDaemon.call_args_list,
            [
                ((True, ), {}),
                ((True, ), {}),
            ]
        )

        self.assertEquals(mock_thread.start.call_args_list,
            [
                ((), {}),
                ((), {}),
            ]
        )

        self.assertCalledOnce(unrecalculated_cell_queue.join)


class TestExecuteUsercode(ResolverTestCase):

    def test_execute_usercode_does(self):
        context = {}
        execute_usercode('x = "test"', context)
        self.assertEquals(context['x'], 'test')


SANITY_CHECK_USERCODE = dedent("""
    load_constants(worksheet)
    %s
    evaluate_formulae(worksheet)
    %s
""")
class TestCalculate(ResolverTestCase):

    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.evaluate_formulae_in_context')
    def test_calculate_should_execute_usercode_with_correct_context_and_curried_evaluate_formulae_in_context(
        self, mock_evaluate_formulae_in_context, mock_execute_usercode
    ):
        worksheet = Worksheet()
        calculate(worksheet, sentinel.usercode, sentinel.private_key)

        args, kwargs = mock_execute_usercode.call_args

        self.assertEquals(kwargs, {})

        self.assertEquals(args[0], sentinel.usercode)

        context = args[1]
        self.assertEquals(context['CellRange'], CellRange)
        self.assertEquals(context['DateTime'], DateTime)
        self.assertEquals(context['FormulaError'], FormulaError)
        self.assertEquals(context['_raise'], _raise)
        self.assertEquals(context['sys'], sys)

        self.assertEquals(context['worksheet'], worksheet)
        self.assertEquals(context['load_constants'], load_constants)
        self.assertEquals(context['undefined'], undefined)
        evaluate_formulae = context['evaluate_formulae']
        evaluate_formulae(sentinel.worksheet)
        self.assertEquals(
            mock_evaluate_formulae_in_context.call_args,
            ((sentinel.worksheet, context), {})
        )

    @patch('sheet.calculate.execute_usercode')
    def test_calculate_patches_sys_stdout_in_context(
        self, mock_execute_usercode
    ):
        worksheet = Worksheet()

        def check_stdout(_, context):
            self.assertEquals(type(context['sys'].stdout), MyStdout)
            self.assertEquals(context['sys'].stdout.worksheet, worksheet)
        mock_execute_usercode.side_effect = check_stdout

        calculate(worksheet, sentinel.usercode, sentinel.private_key)

        self.assertNotEqual(type(sys.stdout), MyStdout)


    def test_mystdout_pushes_print_commands_to_worksheet(self):
        ws = Worksheet()
        mso = MyStdout(ws)
        mso.write('weeeeeee!')
        ws2 = Worksheet()
        ws2.add_console_text('weeeeeee!', log_type='output')
        self.assertEquals(ws._console_text, ws2._console_text)


    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.run_worksheet')
    def test_calculate_puts_curried_run_worksheet_into_context(self, mock_run_worksheet, mock_execute_usercode):
        worksheet = Worksheet()
        calculate(worksheet, sentinel.usercode, sentinel.private_key)
        args, kwargs = mock_execute_usercode.call_args
        context = args[1]
        curried_run_worksheet = context['run_worksheet']
        self.assertEquals(mock_run_worksheet.call_args_list, [])
        curried_run_worksheet(sentinel.urls)
        self.assertCalledOnce(mock_run_worksheet, sentinel.urls, None, sentinel.private_key)

        mock_run_worksheet.reset_mock()
        curried_run_worksheet(sentinel.urls, sentinel.overrides)
        self.assertCalledOnce(mock_run_worksheet, sentinel.urls, sentinel.overrides, sentinel.private_key)


    @patch('sheet.calculate.execute_usercode')
    def test_calculate_clears_previous_worksheet_cell_values_before_executing_usercode(
        self, mock_execute_usercode
    ):
        calls_list = []
        worksheet = Worksheet()
        worksheet.clear_values = Mock()

        worksheet.clear_values.side_effect = lambda *args : calls_list.append('clear values')
        mock_execute_usercode.side_effect  = lambda *args : calls_list.append('execute usercode')

        calculate(worksheet, sentinel.usercode, sentinel.private_key)

        self.assertEquals(calls_list, ['clear values', 'execute usercode'])


    @patch('sheet.calculate.execute_usercode', Mock())
    @patch('sheet.calculate.evaluate_formulae_in_context', Mock())
    @patch('sheet.calculate.time')
    def test_calculate_clears_previous_worksheet_console_text_and_reports_time(self, mock_time):
        recalc_times = [1.3245, 0]
        def mock_time_fn():
            return recalc_times.pop()
        mock_time.side_effect = mock_time_fn
        worksheet = Worksheet()
        worksheet._console_text = 'previous errors'
        worksheet.add_console_text = Mock()

        calculate(worksheet, sentinel.usercode, sentinel.private_key)
        expected_text = 'Took 1.32s'
        self.assertEquals(worksheet.add_console_text.call_args_list[0],
                          ((expected_text,),{'log_type':'system'})
        )


    @patch('sheet.calculate.evaluate_formulae_in_context', Mock())
    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.time')
    def test_calculate_clears_previous_worksheet_console_text_and_reports_time_when_theres_an_error(self, mock_time, mock_execute_usercode):
        recalc_times = [1.3245, 0]
        def mock_time_fn():
            return recalc_times.pop()
        mock_time.side_effect = mock_time_fn
        def throw_error(_, __):
            raise Exception('argh')
        mock_execute_usercode.side_effect = throw_error
        worksheet = Worksheet()
        worksheet._console_text = 'previous errors\n'
        worksheet.add_console_text = Mock()

        calculate(worksheet, sentinel.usercode, sentinel.private_key)

        self.assertNotIn('previous errors', worksheet._console_text)
        self.assertEquals(
            worksheet.add_console_text.call_args_list[-1],
            (('Took 1.32s',),{'log_type':'system'}),
        )

    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.evaluate_formulae_in_context')
    def test_calculate_clears_previous_worksheet_usercode_error(self, mock_evaluate_formulae_in_context, mock_execute_usercode):
        worksheet = Worksheet()
        worksheet._usercode_error = "Argh!"
        calculate(worksheet, sentinel.usercode, sentinel.private_key)
        self.assertEquals(worksheet._usercode_error, None)



    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.evaluate_formulae_in_context', Mock())
    def test_calculate_catches_usercode_exceptions(self, mock_execute_usercode):
        worksheet = Worksheet()
        def execute_usercode(_, __):
            exec('1/0\n')
        mock_execute_usercode.side_effect = execute_usercode
        try:
            calculate(worksheet, sentinel.usercode, sentinel.private_key)
        except:
            self.fail("Unhandled exception when executing broken usercode")


    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.evaluate_formulae_in_context')
    def test_calculate_catches_and_reports_exceptions_in_worksheet_usercode_error_field(self, mock_evaluate_formulae_in_context, mock_execute_usercode):
        worksheet = Worksheet()
        def execute_usercode(_, __):
            exec(
                'import sys\n'
                'def func():\n'
                '    x = my_value\n'
                'func()\n'
            )
        mock_execute_usercode.side_effect = execute_usercode
        calculate(worksheet, sentinel.usercode, sentinel.private_key)
        expected = {
            'message': 'NameError: global name \'my_value\' is not defined',
            'line': 3,
        }
        self.assertEquals(worksheet._usercode_error, expected)


    def test_calculate_catches_and_reports_syntax_errors_with_special_message_in_worksheet_usercode_error_field(self):

        def patched_execute_usercode(_, __):
            exec('import sys:\nx == my_value')
        worksheet = Worksheet()

        original_execute_usercode = calculate_module.execute_usercode
        calculate_module.execute_usercode = patched_execute_usercode
        try:
            calculate(worksheet, sentinel.usercode, sentinel.private_key)
        finally:
            calculate_module.execute_usercode = original_execute_usercode

        expected = {
            'message': 'Syntax error at character 11',
            'line': 1
        }
        self.assertEquals(worksheet._usercode_error, expected)


    def test_calculate_catches_and_reports_exceptions_to_console(self):

        def patched_execute_usercode(_, context):
            exec(
                'import sys\n'
                'def func():\n'
                '    x = my_value\n'
                'func()\n',
                context
            )
        worksheet = Worksheet()
        worksheet.add_console_text = Mock()
        original_execute_usercode = calculate_module.execute_usercode
        calculate_module.execute_usercode = patched_execute_usercode
        try:
            calculate(worksheet, sentinel.usercode, sentinel.private_key)
        finally:
            calculate_module.execute_usercode = original_execute_usercode

        expected_error_text = dedent("""
                    NameError: global name \'my_value\' is not defined
                        User code line 4
                        User code line 3, in func\n""")[1:]
        self.assertIn(
            call(expected_error_text),
            worksheet.add_console_text.call_args_list
        )


    @patch('sheet.calculate.execute_usercode')
    @patch('sheet.calculate.evaluate_formulae_in_context')
    def test_calculate_catches_and_reports_syntax_errors_to_console(self, mock_evaluate_formulae_in_context, mock_execute_usercode):
        worksheet = Worksheet()
        worksheet.add_console_text = Mock()

        def execute_usercode(_, __):
            exec('import sys:\nx == my_value')
        mock_execute_usercode.side_effect = execute_usercode
        calculate(worksheet, sentinel.usercode, sentinel.private_key)

        expected_error_text = 'Syntax error at character 11 (line 1)\n'
        self.assertIn(
            ((expected_error_text,), {}),
            worksheet.add_console_text.call_args_list
        )


    def test_format_traceback_filters_frames_that_are_dirigible_code(self):
        import sheet.worksheet as worksheet_module

        frames = [
            (calculate_module.__file__, 83,
                'calculate', 'execute_usercode(usercode, context)'),
            (calculate_module.__file__, 71,
                'execute_usercode', 'exec(usercode, context)'),
            ("<string>", 14,
                '<module>', None),
            ("<string>", 4,
                'fn', None),
            ("build/bdist.linux-i686/egg/simplejson/__init__.py", 384,
                'loads', None),
            ("build/bdist.linux-i686/egg/simplejson/decoder.py", 402,
                'decode', 'obj, end = self.raw_decode(s, idx=_w(s, 0).end())'),
            (worksheet_module.__file__, 25,
                "__setitem__", 'raise TypeError("Worksheet locations must be Cell objects")'),
        ]

        expected = '''
    User code line 14
    User code line 4, in fn
    File "build/bdist.linux-i686/egg/simplejson/__init__.py" line 384, in loads
    File "build/bdist.linux-i686/egg/simplejson/decoder.py" line 402, in decode
        obj, end = self.raw_decode(s, idx=_w(s, 0).end())'''[1:]

        self.assertEquals(format_traceback(frames), expected)


class TestCalculateWithTimeout(ResolverTestCase):

    @patch('sheet.calculate.calculate')
    def test_calculate_with_timeout_calls_calculate_function_with_contents_and_usercode(
        self, mock_calculate
    ):
        long_timeout_seconds = 100
        calculate_with_timeout(
            sentinel.worksheet, sentinel.usercode,
            long_timeout_seconds, sentinel.private_key
        )

        self.assertEquals(
            mock_calculate.call_args,
            ((sentinel.worksheet, sentinel.usercode, sentinel.private_key), {})
        )


    @patch('sheet.calculate.InterruptableThread')
    def test_calculate_with_timeout_uses_interruptable_thread_with_correct_timeout(
        self, mock_ithread_class
    ):
        mock_ithread_class.return_value = mock_ithread = Mock()
        mock_ithread.isAlive.return_value = False
        calculate_with_timeout(
            sentinel.worksheet, sentinel.usercode,
            sentinel.timeout_seconds, sentinel.private_key
        )
        self.assertEquals(mock_ithread.method_calls,
                          [
                              ('start', (), {}),
                              ('join', (sentinel.timeout_seconds,), {}),
                              ('isAlive', (), {}),
                              ]
                          )


    @patch('sheet.calculate.InterruptableThread')
    @patch('sheet.calculate.sleep')
    def test_calculate_with_timeout_tries_to_interrupt_timed_out_thread(
        self, mock_sleep, mock_ithread_class
    ):
        def check_interrupt_called_first(_):
            self.assertTrue(mock_ithread.interrupt.called)
        mock_sleep.side_effect = check_interrupt_called_first

        mock_ithread_class.return_value = mock_ithread = Mock()
        def set_is_alive():
            mock_ithread.alive = not mock_ithread.alive
            return not mock_ithread.alive
        mock_ithread.isAlive.side_effect = set_is_alive

        calculate_with_timeout(
            sentinel.worksheet, sentinel.usercode,
            sentinel.timeout_seconds, sentinel.private_key
        )
        self.assertEquals(mock_ithread.method_calls,
                          [
                              ('start', (), {}),
                              ('join', (sentinel.timeout_seconds,), {}),
                              ('isAlive', (), {}),
                              ('interrupt', (), {}),
                              ('isAlive', (), {}),
                              ]
                          )
        self.assertEquals(mock_sleep.call_args, ((0.1,), {}))



class TestRaise(ResolverTestCase):

    def test_raise_raises(self):
        exception = Exception("Argh")
        with self.assertRaises(Exception) as mgr:
            _raise(exception)
        self.assertEquals(mgr.exception, exception)



class TestRunWorksheet(ResolverTestCase):

    @patch('sheet.calculate.urllib2')
    @patch('sheet.calculate.api_json_to_worksheet')
    def test_run_worksheet_no_overrides(self, mock_api_json_to_worksheet, mock_urllib2):
        mock_api_json_to_worksheet.return_value = Worksheet()
        worksheet_url = 'ws_url/'
        target_url = '%sv%s/json/' % (worksheet_url, CURRENT_API_VERSION)
        result = run_worksheet(worksheet_url, None, sentinel.private_key)

        self.assertCalledOnce(mock_urllib2.build_opener)
        mock_opener = mock_urllib2.build_opener.return_value

        self.assertCalledOnce(mock_opener.open, target_url, data=urlencode({'dirigible_l337_private_key': sentinel.private_key}))
        mock_urlopen_file = mock_opener.open.return_value

        self.assertCalledOnce(mock_api_json_to_worksheet, mock_urlopen_file.read.return_value)
        self.assertEquals(result, mock_api_json_to_worksheet.return_value)


    @patch('sheet.calculate.urlencode')
    @patch('sheet.calculate.urllib2')
    @patch('sheet.calculate.api_json_to_worksheet')
    def test_run_worksheet_with_overrides(self, mock_api_json_to_worksheet, mock_urllib2, mock_urlencode):
        overrides = {'a1': 55}
        str_overrides = {'a1': '55', 'dirigible_l337_private_key': sentinel.private_key}
        mock_api_json_to_worksheet.return_value = Worksheet()
        worksheet_url = 'ws_url/'
        target_url = '%sv%s/json/' % (worksheet_url, CURRENT_API_VERSION)
        result = run_worksheet(worksheet_url, overrides, sentinel.private_key)

        self.assertCalledOnce(mock_urllib2.build_opener)
        mock_opener = mock_urllib2.build_opener.return_value

        self.assertCalledOnce(mock_urlencode, str_overrides)
        encoded_overrides = mock_urlencode.return_value

        self.assertCalledOnce(mock_opener.open, target_url, data=encoded_overrides)
        mock_urlopen_file = mock_opener.open.return_value

        self.assertCalledOnce(mock_api_json_to_worksheet, mock_urlopen_file.read.return_value)
        self.assertEquals(result, mock_api_json_to_worksheet.return_value)


    @patch('sheet.calculate.urllib2')
    def test_run_worksheet_with_error(self, mock_urllib2):
        mock_opener = mock_urllib2.build_opener.return_value
        mock_urlopen_file = mock_opener.open.return_value
        mock_urlopen_file.read.return_value = '{ "usercode_error" : { "message": "error", "line": "line_no" } }'

        with self.assertRaises(Exception) as mngr:
            run_worksheet('worksheet_url', None, sentinel.private_key)
        self.assertEquals(str(mngr.exception), 'run_worksheet: error')


    @patch('sheet.calculate.urllib2')
    @patch('sheet.calculate.api_json_to_worksheet')
    def test_run_worksheet_passes_private_key_in_params(self, mock_api_json_to_worksheet, mock_urllib2):
        worksheet_url = 'ws_url/'
        target_url = '%sv%s/json/' % (worksheet_url, CURRENT_API_VERSION)
        mock_api_json_to_worksheet.return_value = Worksheet()

        mock_opener = mock_urllib2.build_opener.return_value
        mock_urlopen_file = mock_opener.open.return_value
        mock_urlopen_file.read.return_value = sentinel.worksheet_json

        run_worksheet(worksheet_url, None, sentinel.private_key)

        self.assertCalledOnce(mock_opener.open, target_url, data=urlencode({'dirigible_l337_private_key': sentinel.private_key}))




class TestJsonToWorksheet(ResolverTestCase):

    def test_values(self):
        json = u'''
        {
            "name": "sheetname",
            "1": {
                "2": "abc",
                "3": "123",
                "4": 123,
                "5": [1, 2, 3, 4],
                "6": "unescaped & unicod\xe9"
            }
        }
        '''
        actual = api_json_to_worksheet(json)
        expected = Worksheet()
        expected.name = 'sheetname'
        expected[1, 2].value = 'abc'
        expected[1, 3].value = '123'
        expected[1, 4].value = 123
        expected[1, 5].value = [1, 2, 3, 4]
        expected[1, 6].value = u'unescaped & unicod\xe9'

        self.assertEquals(dict(actual), dict(expected))
        self.assertEquals(actual, expected)


    def test_should_call_worksheets_without_name_untitled(self):
        json = '{"something": "else"}'
        try:
            result = api_json_to_worksheet(json)
        except KeyError:
            self.fail('shouldnt barf on worksheet with no name')
        self.assertEquals(result.name, 'Untitled')


    def test_should_copy_errors_across(self):
        json = '''
            {
                "usercode_error" : {"message": "ohno!", "something": "else"}
            }
        '''
        try:
            result = api_json_to_worksheet(json)
        except KeyError:
            self.fail('shouldnt barf on worksheet with error')
        self.assertTrue(isinstance(result, Worksheet))
        self.assertEquals(
            result._usercode_error,
            {"message": "ohno!", "something": "else"}
        )



class TestCalculateSemiFunctional(ResolverTestCase):

    def test_totally_empty(self):
        worksheet = Worksheet()
        calculate(worksheet, '', sentinel.private_key)
        self.assertEquals(worksheet, Worksheet())


    def test_empty_worksheet(self):
        worksheet = Worksheet()
        calculate(worksheet, SANITY_CHECK_USERCODE % ('', ''), sentinel.private_key)
        self.assertEquals(worksheet, Worksheet())


    def test_constant(self):
        worksheet = Worksheet()
        worksheet[1, 2].formula = '3'
        calculate(worksheet, SANITY_CHECK_USERCODE % ('', ''), sentinel.private_key)
        self.assertEquals(worksheet.keys(), [(1, 2)])
        self.assertEquals(worksheet[(1, 2)].formula, '3')
        self.assertEquals(worksheet[(1, 2)].value, 3)


    def test_multiple_constants(self):
        worksheet = Worksheet()
        worksheet[1, 2].formula = '3'
        worksheet[3, 4].formula = '4+5'
        worksheet[2, 5].formula = 'blurgle'

        calculate(worksheet, SANITY_CHECK_USERCODE % ('', ''), sentinel.private_key)
        self.assertEquals(set(worksheet.keys()), set([(1, 2), (3, 4), (2, 5)]))
        self.assertEquals(worksheet[1, 2].formula, '3')
        self.assertEquals(worksheet[3, 4].formula, '4+5')
        self.assertEquals(worksheet[2, 5].formula, 'blurgle')
        self.assertEquals(worksheet[1, 2].value, 3)
        self.assertEquals(worksheet[3, 4].value, '4+5')
        self.assertEquals(worksheet[2, 5].value, 'blurgle')


    def test_arithmetic(self):
        worksheet = Worksheet()
        worksheet[1, 2].formula = '=3'
        worksheet[3, 4].formula = '=4+5'
        worksheet[4, 4].formula = '=1/10'

        calculate(worksheet, SANITY_CHECK_USERCODE % ('', ''), sentinel.private_key)

        self.assertEquals(set(worksheet.keys()), set([(1, 2), (3, 4), (4, 4)]))
        self.assertEquals(worksheet[1, 2].value, 3)
        self.assertEquals(worksheet[3, 4].value, 9)
        self.assertEquals(worksheet[4, 4].value, 0.1)
        self.assertEquals(worksheet[1, 2].formula, '=3')
        self.assertEquals(worksheet[3, 4].formula, '=4+5')
        self.assertEquals(worksheet[4, 4].formula, '=1/10')


    def test_formulae(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=1'
        worksheet[1, 2].formula = '=2'
        worksheet[1, 3].formula = '=A1 + A2'
        worksheet[1, 4].formula = '=DateTime(2000, 1, 2, 3, 4, 5)'

        calculate(worksheet, SANITY_CHECK_USERCODE % ('', ''), sentinel.private_key)

        self.assertEquals(set(worksheet.keys()), set([(1, 1), (1, 2), (1, 3), (1, 4)]))
        self.assertEquals(worksheet[1, 1].value, 1)
        self.assertEquals(worksheet[1, 2].value, 2)
        self.assertEquals(worksheet[1, 3].value, 3)
        self.assertEquals(worksheet[1, 4].value, datetime(2000, 1, 2, 3, 4, 5))
        self.assertEquals(worksheet[1, 1].formula, '=1')
        self.assertEquals(worksheet[1, 2].formula, '=2')
        self.assertEquals(worksheet[1, 3].formula, '=A1 + A2')
        self.assertEquals(worksheet[1, 4].formula, '=DateTime(2000, 1, 2, 3, 4, 5)')


    def test_python_formulae(self):
        worksheet = Worksheet()
        worksheet[1, 1].python_formula = '1'
        worksheet[1, 2].python_formula = '2'
        worksheet[1, 3].python_formula = '1 + 2'

        calculate(worksheet, SANITY_CHECK_USERCODE % ('', ''), sentinel.private_key)

        self.assertEquals(set(worksheet.keys()), set([(1, 1), (1, 2), (1, 3)]))
        self.assertEquals(worksheet[1, 1].value, 1)
        self.assertEquals(worksheet[1, 2].value, 2)
        self.assertEquals(worksheet[1, 3].value, 3)


    def test_preformula_usercode(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '3'
        worksheet[1, 3].formula = '=A2 + 1'

        preformula_usercode = "worksheet[1, 2].value = worksheet[1, 1].value + 1"
        calculate(worksheet, SANITY_CHECK_USERCODE % (preformula_usercode, ''), sentinel.private_key)

        self.assertEquals(set(worksheet.keys()), set([(1, 1), (1, 2), (1, 3)]))
        self.assertEquals(worksheet[1, 1].value, 3)
        self.assertEquals(worksheet[1, 2].value, 4)
        self.assertEquals(worksheet[1, 3].value, 5)
        self.assertEquals(worksheet[1, 1].formula, '3')
        self.assertEquals(worksheet[1, 2].formula, None)
        self.assertEquals(worksheet[1, 3].formula, '=A2 + 1')


    def test_postformula_usercode(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '=1'
        postformula_usercode = 'worksheet[1, 2].value = worksheet[1, 1].value + 1'

        calculate(worksheet, SANITY_CHECK_USERCODE % ('', postformula_usercode), sentinel.private_key)

        self.assertEquals(set(worksheet.keys()), set([(1, 1), (1, 2)]))
        self.assertEquals(worksheet[1, 1].value, 1)
        self.assertEquals(worksheet[1, 2].value, 2)
        self.assertEquals(worksheet[1, 1].formula, '=1')
        self.assertEquals(worksheet[1, 2].formula, None)


    def test_preformula_usercode_functions(self):
        worksheet = Worksheet()
        worksheet[1, 1].formula = '1'
        worksheet[1, 2].formula = '=foo(3)'

        preformula_usercode = dedent('''
        def foo(value):
            return worksheet[1, 1].value + value
        ''')

        calculate(worksheet, SANITY_CHECK_USERCODE % (preformula_usercode, ''), sentinel.private_key)

        self.assertEquals(set(worksheet.keys()), set([(1, 1), (1, 2)]))
        self.assertEquals(worksheet[1, 1].value, 1)
        self.assertEquals(worksheet[1, 2].value, 4)
        self.assertEquals(worksheet[1, 1].formula, '1')
        self.assertEquals(worksheet[1, 2].formula, '=foo(3)')


    @patch('sheet.calculate.urllib2')
    def test_run_worksheet_should_return_worksheet_with_calculated_values_only(self, mock_urllib2):
        self.maxDiff = None

        original_sheet = Worksheet()

        original_sheet.A2.formula = '1'
        original_sheet.A2.value = 1

        original_sheet.C3.formula = '5'
        original_sheet.C3.value = 5

        original_sheet.E4.formula = '=A2 + C3'
        original_sheet.E4.value = 6

        expected_sheet = Worksheet()
        expected_sheet.name = 'Untitled'
        for (col, row), cell in original_sheet.items():
            expected_sheet[col, row].value = cell.value
        foreign_sheet = Sheet()
        foreign_sheet.owner = User(username='skeletor', password='1havTehpowa')
        foreign_sheet.owner.save()
        foreign_sheet.contents_json = worksheet_to_json(original_sheet)
        foreign_sheet.calculate()

        mock_opener = mock_urllib2.build_opener.return_value
        mock_urlopen_file = mock_opener.open.return_value
        mock_urlopen_file.read.return_value = _sheet_to_value_only_json(
            foreign_sheet.name, worksheet_from_json(foreign_sheet.contents_json)
        )

        worksheet_url = 'ws_url/'
        result = run_worksheet(worksheet_url, None, sentinel.private_key)

        target_url = '%sv%s/json/' % (worksheet_url, CURRENT_API_VERSION)
        self.assertCalledOnce(mock_opener.open, target_url, data=urlencode({'dirigible_l337_private_key': sentinel.private_key}))
        self.assertEquals(type(result), Worksheet)
        self.assertEquals(result, expected_sheet)


    @patch('sheet.calculate.urllib2')
    def test_run_worksheet_with_overrides(self, mock_urllib2):
        self.maxDiff = None

        cellA2 = Cell()
        cellA2.formula = '1'
        cellA2.value = 1

        cellC3 = Cell()
        cellC3.formula = '5'
        cellC3.value = 5

        cellE4 = Cell()
        cellE4.formula = '=A2 + C3'
        cellE4.value = 6

        overrides = {
            (1, 2): '11',
            (3, 3): 55,
            (4, 1): '="abc"',
            'dirigible_l337_private_key': sentinel.private_key
        }

        result_of_calculation_json = '''{
            "name": "Untitled",
            "1": {
                "2": 11
            },
            "3": {
                "3": 55
            },
            "4": {
                "1": "abc"
            },
            "5": {
                "4": 66
            }
        }'''

        mock_opener = mock_urllib2.build_opener.return_value
        mock_urlopen_file = mock_opener.open.return_value
        mock_urlopen_file.read.return_value = result_of_calculation_json

        worksheet_url = 'ws_url/'
        result = run_worksheet(worksheet_url, overrides, sentinel.private_key)

        target_url = '%sv%s/json/' % (worksheet_url, CURRENT_API_VERSION)
        self.assertCalledOnce(mock_opener.open, target_url, data=urlencode(overrides))
        self.assertEquals(type(result), Worksheet)
        expected_sheet = Worksheet()
        expected_sheet.name = 'Untitled'
        expected_sheet[1, 2].value = 11
        expected_sheet[3, 3].value = 55
        expected_sheet[4, 1].value = 'abc'
        expected_sheet[5, 4].value = 66

        self.assertEquals(result, expected_sheet)
