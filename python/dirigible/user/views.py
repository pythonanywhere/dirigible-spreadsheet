# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve, reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
import registration as django_registration

from dirigible.sheet.models import copy_sheet_to_user, Sheet
from dirigible.user.forms import DirigibleRegistrationForm


def copy_sheet_for_new_user_callback(next_url):
    def _inner(user):
        _, __, kwargs = resolve(next_url)
        sheet_id = kwargs['sheet_id']
        copy_sheet_to_user(Sheet.objects.get(id=sheet_id), user)
    return _inner


def register(request):
    form = DirigibleRegistrationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        request.session["email-address"] = email

    kwargs = {
        'form_class': DirigibleRegistrationForm,
    }
    if 'next' in request.POST and request.POST['next']:
        kwargs['profile_callback'] = copy_sheet_for_new_user_callback(
            request.POST['next']
        )
    elif 'next' in request.GET and request.GET['next']:
        kwargs['extra_context'] = {'next': request.GET['next']}

    return django_registration.views.register(request, **kwargs)


def registration_complete(request):
    return direct_to_template(
        request,
        'registration/registration_complete.html',
        extra_context={ 'email_address': request.session.get("email-address") }
    )


def redirect_to_front_page(request):
    return HttpResponseRedirect(reverse('front_page'))


@login_required
def user_dashboard(request):
    sheets = Sheet.objects.filter(owner=request.user)
    return render_to_response('user_page.html', {'user':request.user, 'sheets':sheets})


@login_required
def change_password(request, username):
    if request.user.username != username:
        raise Http404('No User matches the given query.')
    user = get_object_or_404(User, username=username)
    current_password = request.POST.get('id_change_password_current_password', '')
    if not user.check_password(current_password):
        return HttpResponse('Current password incorrect.')

    new_password1 = request.POST.get('id_change_password_new_password', '')
    new_password2 = request.POST.get('id_change_password_new_password_again', '')
    if '' in (new_password1, new_password2) or (new_password1 != new_password2):
        return HttpResponse('Please provide the new password twice for confirmation.')
    user.set_password(new_password1)
    user.save()
    return HttpResponse('Your password has been changed.')
