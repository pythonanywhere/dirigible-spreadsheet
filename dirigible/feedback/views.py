# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from textwrap import dedent

from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings



def submit(request):
    send_mail(
        "User feedback from Dirigible",
        dedent("""
            Username: %s
            Email address: %s
            Page: %s

            Message:
            %s
        """) % (
            request.POST["username"], request.POST["email_address"],
            request.META['HTTP_REFERER'], request.POST["message"]
        ),
        settings.SERVER_EMAIL,
        [settings.FEEDBACK_EMAIL]
    )
    return HttpResponse("OK")
