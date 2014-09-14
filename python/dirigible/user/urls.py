# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.conf.urls.defaults import include, patterns, url

from user.views import change_password, redirect_to_front_page


urlpatterns = patterns(
    '',
    url(
        r'^[^/]+/$',
        redirect_to_front_page,
        name="user_page"
    ),

    url(
        r'^(?P<username>[^/]+)/sheet/',
        include('sheet.urls'),
    ),

    url(
        r'^(?P<username>[^/]+)/change_password/$',
        change_password,
        name="change_password"
    ),

)
