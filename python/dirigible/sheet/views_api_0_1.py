# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import simplejson as json
from datetime import datetime, timedelta
from urllib2 import HTTPError

from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404

from sheet.cell import undefined
from sheet.models import Sheet
from sheet.utils.cell_name_utils import cell_ref_as_string_to_coordinates
from sheet.views import rollback_on_exception
from user.models import OneTimePad


@transaction.commit_manually
@rollback_on_exception
def calculate_and_get_json_for_api(request, username, sheet_id):
    sheet = get_object_or_404(Sheet, pk=sheet_id, owner__username=username)
    pads = None

    if request.method == 'POST':
        params = request.POST
    else:
        params = request.GET

    if 'api_key' in params:
        if not sheet.allow_json_api_access:
            return HttpResponseForbidden()
        elif params['api_key'] != sheet.api_key:
            return HttpResponseForbidden()
    elif 'dirigible_l337_private_key' in params:
        pads = OneTimePad.objects.filter(
                user=sheet.owner,
                guid=params['dirigible_l337_private_key'])
        too_old = datetime.now() - timedelta(36000)
        if len(pads) != 1 or pads[0].creation_time < too_old:
            return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()

    worksheet = sheet.unjsonify_worksheet()
    for encoded_loc, new_formula in params.items():
        colrow = cell_ref_as_string_to_coordinates(encoded_loc)
        if colrow is not None:
            col, row = colrow
            worksheet.set_cell_formula(col, row, new_formula)
    sheet.jsonify_worksheet(worksheet)

    try:
        sheet.calculate()
        worksheet = sheet.unjsonify_worksheet()
        if worksheet._usercode_error:
            return HttpResponse(json.dumps({
                "usercode_error" : {
                    "message" : worksheet._usercode_error["message"],
                    "line" : str(worksheet._usercode_error["line"])
                }
            }))
        response = HttpResponse(
            _sheet_to_value_only_json(sheet.name, worksheet))
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except (Exception, HTTPError), e:
        return HttpResponse(str(e))
    finally:
        transaction.commit()


def _sheet_to_value_only_json(sheet_name, worksheet):
    result = {'name': sheet_name}
    for (col, row), cell in worksheet.items():
        col_dict = result.setdefault(col, {})
        if cell.value is not undefined:
            col_dict[row] = cell.value
    return json.dumps(result, default=unicode)
