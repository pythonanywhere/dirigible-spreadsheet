# Copyright (c) 2011 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
from django.contrib.auth.models import User

from dirigible.test_utils import ResolverTestCase
from sheet.models import Sheet

from featured_sheet.models import FeaturedSheet


class TestFeaturedSheetModel(ResolverTestCase):

    def test_can_construct_without_more_info_url(self):
        user = User(username='featurer')
        user.save()
        sheet = Sheet(owner=user, name='sheet to feature')
        sheet.save()

        description = 'twas brillig and the slithy toves'
        fs = FeaturedSheet(sheet=sheet, description=description)
        fs.save()

        self.assertEquals(fs.sheet, sheet)
        self.assertEquals(fs.description, description)
        self.assertEquals(fs.more_info_url, '')


    def test_can_construct_with_more_info_url(self):
        user = User(username='chattyfeaturer')
        user.save()
        sheet = Sheet(owner=user, name='sheet to feature')
        sheet.save()

        description = 'twas brillig and the slithy toves'
        more_info_url = 'http://far.away/'
        fs = FeaturedSheet(sheet=sheet, description=description, more_info_url=more_info_url)
        fs.save()

        self.assertEquals(fs.sheet, sheet)
        self.assertEquals(fs.description, description)
        self.assertEquals(fs.more_info_url, more_info_url)


    def test_unicode(self):
        user = User(username='printyfeaturer')
        user.save()
        sheet = Sheet(owner=user, name='sheet to feature')
        sheet.save()

        description = 'twas brillig and the slithy toves'
        more_info_url = 'http://far.away/'
        fs = FeaturedSheet(sheet=sheet, description=description, more_info_url=more_info_url)
        fs.save()

        self.assertEquals(unicode(fs), u'Feature: %s' % (sheet.name,))

