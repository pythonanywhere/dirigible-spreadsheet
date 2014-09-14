# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.conf.urls.defaults import *

from .views import (
    calculate, clear_cells, clipboard, copy_sheet, export_csv, get_json_grid_data_for_ui,
    get_json_meta_data_for_ui, import_csv, import_xls, page, set_cell_formula,
    set_column_widths, set_sheet_name, set_sheet_security_settings,
    set_sheet_usercode
)


URL_BASE = r'^(?P<sheet_id>\d+)/'

# Included from users URLs file, so we already have a
# username parameter before any parameters we capture
# here.
urlpatterns = patterns('',

    url(
        '%s$' % URL_BASE,
        page,
        name="sheet_page"
    ),


    url(
        '%scalculate/$' % URL_BASE,
        calculate,
        name="sheet_calculate"
    ),


    url(
        '%sget_json_grid_data_for_ui/$' % URL_BASE,
        get_json_grid_data_for_ui,
        name="sheet_get_json_grid_data_for_ui"
    ),

    url(
        '%sget_json_meta_data_for_ui/$' % URL_BASE,
        get_json_meta_data_for_ui,
        name="sheet_get_json_meta_data_for_ui"
    ),


    url(
        "%simport_csv/$" % URL_BASE,
        import_csv,
        name="sheet_import_csv"
    ),

    url(
        "%sexport_csv/(?P<csv_format>excel|unicode)/$" % URL_BASE,
        export_csv,
        name="sheet_export_csv"
    ),

    url(
        "import_xls/$",
        import_xls,
        name="sheet_import_xls"
    ),


    url(
        "%scopy_sheet/$" % URL_BASE,
        copy_sheet,
        name="sheet_copy_sheet"
    ),


    url(
        '%sset_cell_formula/$' % URL_BASE,
        set_cell_formula,
        name="sheet_set_cell_formula"
    ),

    url(
        '%sset_column_widths/$' % URL_BASE,
        set_column_widths,
        name="sheet_set_column_widths"
    ),

    url(
        "%sset_sheet_name/$" % URL_BASE,
        set_sheet_name,
        name="sheet_set_sheet_name"
    ),

    url(
        '%sset_sheet_usercode/$' % URL_BASE,
        set_sheet_usercode,
        name="sheet_set_sheet_usercode"
    ),

    url(
        '%sset_sheet_security_settings/$' % URL_BASE,
        set_sheet_security_settings,
        name="sheet_set_sheet_security_settings"
    ),


    url(
        '%scut/$' % URL_BASE,
        lambda *args, **kwargs: clipboard(action='cut', *args, **kwargs),
        name="sheet_cut"
    ),

    url(
        '%scopy/$' % URL_BASE,
        lambda *args, **kwargs: clipboard(action='copy', *args, **kwargs),
        name="sheet_copy"
    ),

    url(
        '%spaste/$' % URL_BASE,
        lambda *args, **kwargs: clipboard(action='paste', *args, **kwargs),
        name="sheet_paste"
    ),


    url(
        '%sclear_cells/$' % URL_BASE,
        clear_cells,
        name="sheet_clear_cells"
    ),


    url(
        r'%sv0\.1/' % (URL_BASE,),
        include('sheet.urls_api_0_1'),
    ),

)
