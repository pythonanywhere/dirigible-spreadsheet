# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
from mock import patch
from datetime import datetime

from django.contrib.auth.models import AnonymousUser, User

from test_utils import ResolverTestCase
from user.models import AnonymousProfile, OneTimePad, UserProfile


class TestOneTimePads(ResolverTestCase):

    @patch('user.models.uuid4')
    def test_OneTimePad_init(self, mock_uuid4):
        user = User(username='Alice, traditionally')
        user.save()
        otp = OneTimePad(user=user)
        otp.save()
        otp = OneTimePad.objects.get(pk=otp.id)
        self.assertTrue( (datetime.now() - otp.creation_time).seconds < 1)
        self.assertEquals(otp.user, user)
        self.assertEquals(otp.guid, unicode(mock_uuid4.return_value))



class TestUserProfiles(ResolverTestCase):

    def test_defaults(self):
        user_profile = UserProfile()
        self.assertEquals(user_profile.has_seen_sheet_page, False)


    def test_save_new_user_creates_user_profile(self):
        user = User(username='Kenny Ken')
        user.save()
        self.assertEquals(type(user.get_profile()), UserProfile)
        self.assertEquals(user.get_profile().user, user)


class TestAnonymousUser(ResolverTestCase):

    def test_anonymous_user_has_a_profile(self):
        profile = AnonymousUser().get_profile()
        self.assertEquals(type(profile), AnonymousProfile)

    def test_anonymous_user_attrs(self):
        self.assertIsNone(AnonymousUser().email)

    def test_anonymous_profile_attrs(self):
        profile = AnonymousUser().get_profile()
        self.assertTrue(profile.has_seen_sheet_page)
        self.assertIsNone(profile.save())

