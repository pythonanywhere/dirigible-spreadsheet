import os
from dirigible.test_utils import *
from dirigible.sheet.tests.test_sheet import *
from dirigible.sheet.tests.test_clipboard import *
from dirigible.sheet.tests.test_calculate import *
from dirigible.sheet.tests.test_calculate_server import *
from dirigible.sheet.tests.test_cell import *
from dirigible.sheet.tests.test_cell_range import *
from dirigible.sheet.tests.test_dirigible_datetime import *
from dirigible.sheet.tests.test_dependency_graph import *
from dirigible.sheet.tests.test_eval_constant import *
from dirigible.sheet.tests.test_errors import *
from dirigible.sheet.tests.test_formula_interpreter import *
from dirigible.sheet.tests.test_importer import *
from dirigible.sheet.tests.test_worksheet import *
from dirigible.sheet.tests.test_forms import *
from dirigible.sheet.tests.test_rewrite_formula_offset_cell_references import *
from dirigible.sheet.tests.test_views import *
from dirigible.sheet.tests.test_views_api_0_1 import *
from dirigible.sheet.tests.test_ui_jsonifier import *
from dirigible.sheet.tests.utils.test_cell_name_utils import *
from dirigible.sheet.tests.utils.test_process_utils import *

suite = create_suite_for_file_directory(os.path.dirname(__file__))


