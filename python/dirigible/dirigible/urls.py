# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
import os

from django.conf.urls.defaults import *

from django.contrib import admin
from django.views.generic.simple import direct_to_template

from settings import LOGIN_URL

from dirigible.info_pages.views import front_page_view, info_page_view
from dirigible.featured_sheet.models import FeaturedSheet
from dirigible.shared.views import redirect_to
from dirigible.sheet.views import new_sheet

admin.autodiscover()

urlpatterns = patterns('',

    url(
        r'^$',
        front_page_view,
        name='front_page'
    ),

    url(
        r'^(?P<template_name>oss|video)/',
        info_page_view,
        name="info_page"
    ),

    url(r'^admin/', include(admin.site.urls)),

    url(
        r'^blog/$',
        redirect_to,
        { 'url' : '/' }
    ),

    url(
        r'^featured_sheets/$',
        direct_to_template,
        {'template': 'featured_sheets.html', 'extra_context': {'sheets': FeaturedSheet.objects.all}},
        name='featured_sheets'
    ),

    url(
        # If you change this, don't forget to change the LOGIN_URL in settings.py
        # Here be dragons. The settings .py one has no trailing slash and needs to
        # stay that way. Changing either of these will stop it from working in Chrome
        # and in Firefox if you press ENTER to login.
        r'^login/',
        'django.contrib.auth.views.login',
        {'template_name': 'login.html'},
        name="login"
    ),

    url(
        r'^logout$',
        'django.contrib.auth.views.logout',
        { 'next_page' : LOGIN_URL },
        name="logout"
    ),

    url(
        r'^new_sheet$',
        new_sheet,
        name="new_sheet"
    ),

    url(
        r'^user/',
        include('dirigible.user.urls')
    ),

    url(
        r'^signup/',
        include('dirigible.user.signup_urls')
    ),

    url(
        r'^feedback/',
        include('dirigible.feedback.urls')
    ),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(os.path.dirname(__file__), '..', '..', 'static')}
    ),
)
