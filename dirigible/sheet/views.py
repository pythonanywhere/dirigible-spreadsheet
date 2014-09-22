# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from functools import wraps
import json
import os
from os.path import splitext
from tempfile import mkstemp
import xlrd

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.utils.html import escape

from .forms import ImportCSVForm
from .models import Clipboard, Sheet, copy_sheet_to_user
from .ui_jsonifier import (
    sheet_to_ui_json_grid_data, sheet_to_ui_json_meta_data
)
from .worksheet import worksheet_to_csv
from .importer import (
    DirigibleImportError, worksheet_from_csv, worksheet_from_excel
)
from user.models import AnonymousUser


def fetch_users_sheet(view):
    def _fetch_users_sheet_if_permitted(request, username, sheet_id, *args, **kwargs):
        sheet = get_object_or_404(Sheet, pk=sheet_id, owner__username=username)
        if sheet.owner != request.user:
            if not request.user.is_staff:
                return HttpResponseForbidden(render_to_string("403.html"))
        return view(request, sheet, *args, **kwargs)
    return _fetch_users_sheet_if_permitted


def fetch_users_or_public_sheet(view):

    def _fetch_sheet_if_permitted(request, username, sheet_id, *args, **kwargs):
        sheet = get_object_or_404(Sheet, pk=sheet_id, owner__username=username)
        if not sheet.is_public:
            if isinstance(request.user, AnonymousUser):
                sheet_url = reverse('sheet_page', args=(username, sheet_id))
                return HttpResponseRedirect('/login?next=/%s' % (sheet_url,))
            elif sheet.owner != request.user and not request.user.is_staff:
                return HttpResponseForbidden(render_to_string("403.html"))

        sheet.public_view_mode = (sheet.owner != request.user)

        return view(request, sheet, *args, **kwargs)

    return _fetch_sheet_if_permitted



def rollback_on_exception(view):
    @wraps(view)
    def _rollback_on_exception(*args, **kwargs):
        transaction.set_autocommit(False)
        try:
            return view(*args, **kwargs)
        except:
            transaction.rollback()
            raise
        finally:
            transaction.set_autocommit(True)
    return _rollback_on_exception


def update_sheet_with_version_check(sheet, **kwargs):
    query = Q(id=sheet.id) & Q(version=sheet.version)
    sheets_updated = Sheet.objects.filter(query).update(version=sheet.version + 1, **kwargs)
    return sheets_updated != 0


@login_required
def import_xls(request, username):
    if request.user.username != username:
        return HttpResponseForbidden(render_to_string("403.html"))

    handle, filename = mkstemp()
    try:
        os.write(handle, request.FILES['file'].read())
        wb = xlrd.open_workbook(filename)
        for xl_sheet in wb.sheets():
            if xl_sheet.nrows > 0 and xl_sheet.ncols > 0:
                name = '%s - %s' % (
                    splitext(request.FILES['file'].name)[0],
                    xl_sheet.name
                )
                sheet = Sheet(owner=request.user, name=name)
                sheet.jsonify_worksheet(worksheet_from_excel(xl_sheet))
                sheet.save()

                try:
                    calculate(request, sheet.owner.username, sheet.id)
                except:
                    pass

    except Exception:
        return render(
            request,
            'import_xls_error.html',
            {},
            context_instance=RequestContext(request)
        )
    finally:
        os.close(handle)
        os.unlink(filename)
    return HttpResponseRedirect('/')


@fetch_users_or_public_sheet
def export_csv(request, sheet, csv_format):
    if csv_format == 'unicode':
        encoding = 'utf-8'
    else:
        encoding = 'windows-1252'

    try:
        content = worksheet_to_csv(
            sheet.unjsonify_worksheet(),
            encoding=encoding
        )
    except UnicodeEncodeError:
        return render(
            request,
            'export_csv_error.html',
            {'sheet': sheet},
            context_instance=RequestContext(request)
        )

    response = HttpResponse(content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % (sheet.name,)
    response['Content-Length'] = len(content)
    return response


@login_required
@fetch_users_sheet
def import_csv(request, sheet):
    def error_response():
        return render(
            request,
            'import_csv_error.html',
            {'sheet': sheet},
            context_instance=RequestContext(request)
        )

    form = ImportCSVForm(request.POST, request.FILES)
    if not form.is_valid():
        return error_response()

    worksheet = sheet.unjsonify_worksheet()
    csv_file = request.FILES['file']
    column = form.cleaned_data['column']
    row = form.cleaned_data['row']
    excel_file_encoding = request.POST['csv_encoding']=='excel'
    try:
        worksheet = worksheet_from_csv(
            worksheet, csv_file, column, row, excel_file_encoding
        )
    except DirigibleImportError:
        return error_response()

    sheet.jsonify_worksheet(worksheet)
    if update_sheet_with_version_check(sheet, contents_json=sheet.contents_json):
        calculate(request, sheet.owner.username, sheet.id)
        return HttpResponseRedirect(reverse('sheet_page',kwargs={
                'username' : request.user.username,
                'sheet_id' : sheet.id,
        }))
    else:
        return HttpResponse('FAILED')


@login_required
@fetch_users_or_public_sheet
def copy_sheet(request, sheet):
    copied_sheet = copy_sheet_to_user(sheet, request.user)
    return HttpResponseRedirect(reverse('sheet_page', kwargs={
        'username': request.user.username,
        'sheet_id': copied_sheet.id
    }))


@login_required
def new_sheet(request):
    sheet = Sheet(owner=request.user)
    sheet.save()
    # need response redirect in order to reset url
    return HttpResponseRedirect(reverse('sheet_page', kwargs={
        'username': request.user.username,
        'sheet_id': sheet.id
    }))


@fetch_users_or_public_sheet
def page(request, sheet):
    profile = request.user.get_profile()
    response = render(
        request,
        'sheet_page.html',
        {
            'sheet': sheet,
            'user': request.user,
            'profile': profile,
            'import_form': ImportCSVForm()
        }
    )
    if not profile.has_seen_sheet_page:
        profile.has_seen_sheet_page = True
        profile.save()

        context = Context(dict(user=request.user))
        email_text = get_template('welcome_email.txt').render(context)
        send_mail(
            'Welcome to Dirigible',
            email_text,
            '',
            [request.user.email],
            fail_silently=True
        )
    return response


@login_required
@fetch_users_sheet
def set_cell_formula(request, sheet):
    column = int(request.POST["column"])
    row = int(request.POST["row"])
    formula = request.POST["formula"]
    worksheet = sheet.unjsonify_worksheet()
    worksheet.set_cell_formula(column, row, formula)
    sheet.jsonify_worksheet(worksheet)
    if update_sheet_with_version_check(sheet, contents_json=sheet.contents_json):
        response = 'OK'
    else:
        response = 'FAILED'
    return HttpResponse(response)


@login_required
@fetch_users_sheet
def clear_cells(request, sheet):
    positions = tuple(map(int, request.POST['range'].split(',')))
    start_col, start_row, end_col, end_row = positions

    worksheet = sheet.unjsonify_worksheet()
    worksheet.cell_range((start_col, start_row), (end_col, end_row)).clear()
    sheet.jsonify_worksheet(worksheet)

    if update_sheet_with_version_check(sheet, contents_json=sheet.contents_json):
        return HttpResponse('OK')
    else:
        return HttpResponse('FAILED')


@login_required
@fetch_users_sheet
def set_sheet_usercode(request, sheet):
    usercode = request.POST['usercode'].replace('\r\n', '\n')
    if update_sheet_with_version_check(sheet, usercode=usercode):
        return HttpResponse('OK')
    else:
        return HttpResponse('FAILED')


@login_required
@fetch_users_sheet
def set_sheet_name(request, sheet):
    sheet.name = request.POST['new_value']
    sheet.save()
    return HttpResponse('{"is_error":false, "html":"%s"}' % (escape(sheet.name,)))


@login_required
@fetch_users_sheet
def set_column_widths(request, sheet):
    sheet.column_widths.update(json.loads(request.POST['column_widths']))
    sheet.save()
    return HttpResponse('OK')


@login_required
@fetch_users_sheet
def set_sheet_security_settings(request, sheet):
    sheet.api_key = request.POST['api_key']
    sheet.allow_json_api_access = request.POST['allow_json_api_access'] == 'true'
    sheet.is_public = request.POST['is_public'] == 'true'
    sheet.save()
    return HttpResponse('OK')


@fetch_users_or_public_sheet
def get_json_grid_data_for_ui(request, sheet):
    rnge = tuple(map(int, request.GET['range'].split(',')))
    return HttpResponse(sheet_to_ui_json_grid_data(sheet.unjsonify_worksheet(), rnge))


@fetch_users_or_public_sheet
def get_json_meta_data_for_ui(request, sheet):
    return HttpResponse(sheet_to_ui_json_meta_data(sheet, sheet.unjsonify_worksheet()))


@never_cache
@login_required
@fetch_users_sheet
@rollback_on_exception
def calculate(request, sheet):
    sheet.calculate()

    transaction.commit()
    sheet_in_db = Sheet.objects.get(pk=sheet.id)
    sheet.merge_non_calc_attrs(sheet_in_db)

    if update_sheet_with_version_check(sheet, contents_json=sheet.contents_json):
        result = HttpResponse('OK')
    else:
        result = HttpResponse('{ "message": "Recalc aborted: sheet changed" }')
    transaction.commit()
    return result


@login_required
@fetch_users_sheet
def clipboard(request, sheet, action):
    clipboard, clipboard_blank = Clipboard.objects.get_or_create(owner=request.user)
    positions = tuple(map(int, request.POST['range'].split(',')))
    start_col, start_row, end_col, end_row = positions

    if action == 'copy':
        clipboard.copy(sheet, (start_col, start_row), (end_col, end_row))
        clipboard.save()
        return HttpResponse('OK')

    elif action == 'cut':
        clipboard.cut(sheet, (start_col, start_row), (end_col, end_row))
        if update_sheet_with_version_check(sheet, contents_json=sheet.contents_json):
            clipboard.save()
            return HttpResponse('OK')
        else:
            return HttpResponse('{ "message": "Cut aborted: sheet changed" }')

    elif action == 'paste':
        if clipboard_blank:
            return HttpResponse('{ "message": "Clipboard blank" }')

        clipboard.paste_to(sheet, (start_col, start_row), (end_col, end_row))
        if update_sheet_with_version_check(sheet, contents_json=sheet.contents_json):
            clipboard.save()
            result = HttpResponse('OK')
        else:
            result = HttpResponse('{ "message": "Paste aborted: sheet changed" }')
        return result

