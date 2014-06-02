# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.conf.urls.defaults import *

from dirigible.feedback.views import submit


urlpatterns = patterns('',

    url(
        r'^submit/$',
        submit,
        name="feedback_submit"
    ),

)
