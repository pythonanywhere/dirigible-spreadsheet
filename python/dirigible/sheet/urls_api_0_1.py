# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.conf.urls.defaults import *

from sheet.views_api_0_1 import calculate_and_get_json_for_api


urlpatterns = patterns('',

    url(
        r'^json/$',
        calculate_and_get_json_for_api,
        name='api_v0.1_get_sheet_json'
    ),
)
