# Copyright (c) 2011 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.db import models

from sheet.models import Sheet

class FeaturedSheet(models.Model):
    sheet = models.ForeignKey(Sheet)
    description = models.TextField()
    more_info_url = models.CharField(max_length=1024, default='', blank=True)

    def __unicode__(self):
        return 'Feature: %s' % (self.sheet.name,)
