import os

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView

from info_pages.views import front_page_view, info_page_view
from sheet.views import new_sheet


urlpatterns = patterns(
    '',

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
        {'next_page': settings.LOGIN_URL},
        name="logout"
    ),

    url(
        r'^new_sheet$',
        new_sheet,
        name="new_sheet"
    ),

    url(
        r'^user/',
        include('user.urls')
    ),

    url(
        r'^signup/',
        include('user.signup_urls')
    ),


    url(
        r'^feedback/',
        include('feedback.urls')
    ),


    url(
        r'^featured_sheets/$',
        TemplateView.as_view(template_name='featured_sheets.html'),#, context={'sheets': FeaturedSheet.objects.all}),
        name='featured_sheets'
    ),

    url(r'^admin/', include(admin.site.urls)),

)
