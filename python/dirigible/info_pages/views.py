# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.shortcuts import render_to_response

from user.views import user_dashboard


def front_page_view(request):
    if request.user.is_authenticated():
        return user_dashboard(request)
    else:
        return non_logged_in_front_page_view(request)


def non_logged_in_front_page_view(request):
    return render_to_response('non_logged_in_front_page.html', {})


def info_page_view(request, template_name):
    return render_to_response('%s.html' % (template_name,), { 'user': request.user })
