# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from uuid import uuid4

from django.contrib.auth.models import AnonymousUser, User
from django.db import models

def get_uid():
    return uuid4()

class OneTimePad(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    guid = models.CharField(default=get_uid, max_length=72)


class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    has_seen_sheet_page = models.BooleanField(default=False)

AnonymousUser.email = None

class AnonymousProfile(object):
    has_seen_sheet_page = True
    save = lambda _: None

User.get_profile = lambda u: UserProfile.objects.get_or_create(user=u)[0]
AnonymousUser.get_profile = lambda u: AnonymousProfile()
