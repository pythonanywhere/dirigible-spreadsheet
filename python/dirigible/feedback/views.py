# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from textwrap import dedent

from django.core.mail import send_mail
from django.http import HttpResponse

from dirigible.settings import FEEDBACK_EMAIL, SERVER_EMAIL


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
        SERVER_EMAIL,
        [FEEDBACK_EMAIL]
    )
    return HttpResponse("OK")
