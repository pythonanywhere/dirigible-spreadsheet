# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from dirigible.user.models import OneTimePad, User, UserProfile


admin.site.register(OneTimePad)

admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile

def has_seen_sheet_page(user):
    return user.get_profile().has_seen_sheet_page

has_seen_sheet_page.boolean = True

class MyUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined', 'last_login', has_seen_sheet_page)

admin.site.register(User, MyUserAdmin)

