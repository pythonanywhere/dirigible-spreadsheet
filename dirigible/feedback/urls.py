# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.conf.urls import *

from feedback.views import submit


urlpatterns = patterns('',

    url(
        r'^submit/$',
        submit,
        name="feedback_submit"
    ),

)
