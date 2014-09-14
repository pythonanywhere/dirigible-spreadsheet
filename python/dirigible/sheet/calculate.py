# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import division


import jsonlib
from Queue import Queue
import sys
from threading import Thread
from time import sleep, time
import traceback
from urllib import urlencode
import urllib2

NUM_THREADS = 10

# API version used by internal calls
CURRENT_API_VERSION = '0.1'

from dirigible.sheet.cell import undefined
from dirigible.sheet.dirigible_datetime import DateTime
from dirigible.sheet.dependency_graph import build_dependency_graph
from dirigible.sheet.eval_constant import eval_constant
from dirigible.sheet.parser import FormulaError
from dirigible.sheet.worksheet import CellRange, Worksheet
from dirigible.sheet.utils.cell_name_utils import coordinates_to_cell_name
from dirigible.sheet.utils.interruptable_thread import InterruptableThread


INF = 1e9999
NEG_INF = -INF


def is_nan(value):
    return isinstance(value, float) and value != value


class MyStdout(object):
    def write(self, text):
        self.worksheet.add_console_text(text, log_type='output')

    def __init__(self, worksheet):
        self.worksheet = worksheet


def load_constants(worksheet):
    for loc in worksheet.iterkeys():
        formula = worksheet[loc].formula
        if formula:
            if not formula.startswith('='):
                worksheet[loc].value = eval_constant(formula)
                worksheet[loc].error = None


def set_cell_error_and_add_to_console(worksheet, location, exception):
    cell = worksheet[location]
    cell.value = undefined
    cell.error = "%s: %s" % (exception.__class__.__name__, str(exception))
    worksheet.add_console_text("%s\n    Formula '%s' in %s\n" % (
            cell.error, cell.formula, coordinates_to_cell_name(*location)))


def recalculate_cell(location, leaf_queue, graph, context):
    cell = context['worksheet'][location]
    cell.error = None
    try:
        cell.value = eval(cell.python_formula, context)
    except Exception, exc:
        set_cell_error_and_add_to_console(context['worksheet'], location, exc)

    graph[location].remove_from_parents(
        [graph[parent_loc] for parent_loc in graph[location].parents],
        leaf_queue
    )


def create_cell_recalculator(leaf_queue, unrecalculated_queue, graph, context):
    def cell_recalculator():
        while not unrecalculated_queue.empty():
            try:
                leaf = leaf_queue.get(block=True,timeout=0.1)
            except:
                continue
            try:
                recalculate_cell(leaf, leaf_queue, graph, context)
            finally:
                leaf_queue.task_done()
                unrecalculated_queue.get()
                unrecalculated_queue.task_done()
    return cell_recalculator


def evaluate_formulae_in_context(worksheet, context):
    graph, leaves = build_dependency_graph(worksheet)
    leaf_queue = Queue()
    unrecalculated_queue = Queue()
    for _ in graph:
        unrecalculated_queue.put(1)

    for _ in range(NUM_THREADS):
        recalculator_thread = Thread(target=create_cell_recalculator(leaf_queue, unrecalculated_queue, graph, context))
        recalculator_thread.setDaemon(True)
        recalculator_thread.start()

    for leaf in leaves:
        leaf_queue.put(leaf)

    unrecalculated_queue.join()


def execute_usercode(usercode, context):
    exec(usercode, context)


def calculate_with_timeout(worksheet, usercode, timeout_seconds, private_key):
    it = InterruptableThread(target=calculate, args=(worksheet, usercode, private_key))
    it.start()
    it.join(timeout_seconds)
    while it.isAlive():
        it.interrupt()
        sleep(0.1)


def calculate(worksheet, usercode, private_key):
    recalc_start = time()
    _calculate(worksheet, usercode, private_key)
    recalc_length = time() - recalc_start
    worksheet.add_console_text('Took %.2fs' % (recalc_length,), log_type='system')


def _calculate(worksheet, usercode, private_key):
    worksheet.clear_values()
    worksheet._console_text = ''
    worksheet._usercode_error = None

    context = {
        'worksheet': worksheet,
        'load_constants': load_constants,
        'undefined': undefined,

        'CellRange': CellRange,
        'DateTime': DateTime,
        'FormulaError': FormulaError,
        '_raise': _raise,
        'sys': sys,
    }
    context['run_worksheet'] = lambda url, overrides=None: run_worksheet(url, overrides, private_key)
    context['evaluate_formulae'] = lambda worksheet: evaluate_formulae_in_context(worksheet, context)
    sys.stdout = MyStdout(worksheet)

    try:
        execute_usercode(usercode, context)
    except Exception, e:
        if isinstance(e, SyntaxError):
            error = 'Syntax error at character %d' % (e.offset,)
            line_no = e.lineno
            worksheet.add_console_text("%s (line %s)\n" % (error, line_no))
        else:
            error = "%s: %s" % (type(e).__name__, str(e))
            tb = sys.exc_info()[2]
            line_no = traceback.extract_tb(tb)[-1][1]
            worksheet.add_console_text("%s\n%s\n" % (error, format_traceback(traceback.extract_tb(tb))))
        worksheet._usercode_error = {"message": error, "line": line_no}


def format_traceback(frames):

    def frame_is_visible_to_user(frame):
        filename, _, function, __ = frame
        return not '/python/dirigible/' in filename


    def format_frame(frame):
        filename, line_no, function, source = frame
        if filename == '<string>':
            filename = '    User code'
        else:
            filename = '    File "%s"' % (filename,)
        if function == '<module>':
            function = ''
        else:
            function = ', in %s' % (function,)
        if source is None:
            source = ''
        else:
            source = '\n        %s' % (source,)
        return "%s line %d%s%s" % (filename, line_no, function, source)

    return '\n'.join(
        map(format_frame,
            filter(frame_is_visible_to_user, frames)
        )
    )


def _raise(exc):
    raise exc


def run_worksheet(worksheet_url, overrides, private_key):
    target_url = '%sv%s/json/' % (worksheet_url, CURRENT_API_VERSION)
    opener = urllib2.build_opener()
    parameters = {}
    parameters['dirigible_l337_private_key'] = private_key
    if overrides is not None:
        str_overrides = dict((loc, str(value)) for loc, value in overrides.iteritems())
        parameters.update(str_overrides)
    sheet_reader = opener.open(target_url, data=urlencode(parameters))
    sheet = api_json_to_worksheet(sheet_reader.read())
    if sheet._usercode_error:
        raise Exception('run_worksheet: %s' % (sheet._usercode_error['message'],))
    return sheet


def api_json_to_worksheet(sheet_json):
    sheet_values = jsonlib.loads(sheet_json)
    worksheet = Worksheet()

    worksheet.name = sheet_values.get('name', 'Untitled')
    for key, value in sheet_values.iteritems():
        if key == "usercode_error":
            worksheet._usercode_error = value
        elif isinstance(value, dict):
            rows = value
            col = int(key)
            for row, value in rows.iteritems():
                row = int(row)
                worksheet[col, row].value = value
    return worksheet
