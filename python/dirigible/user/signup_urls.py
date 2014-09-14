# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.conf.urls.defaults import *
from registration.views import activate

from user.views import register, registration_complete


urlpatterns = patterns('',

    url(
        r'^register/$',
        register,
        name="registration_register"
    ),

    url(
        r'^activate/(?P<activation_key>\w+)/$',
        activate,
        name='registration_activate'
    ),

    url(
        r'^register/complete/$',
        registration_complete,
        name='registration_complete'
    ),

)
