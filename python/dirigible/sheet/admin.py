# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
from dirigible.sheet.models import Sheet
from django.contrib import admin


class SheetAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'name')
    list_filter = ('owner',)

admin.site.register(Sheet, SheetAdmin)

