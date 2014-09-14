# Copyright (c) 2010 Resolver Systems Ltd.
# All Rights Reserved
#

import sys
import os
from textwrap import dedent

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import tempfile


try:
    # python 2.6 with installed unittest2
    from unittest2 import defaultTestLoader, TestSuite
except ImportError:
    # python 2.7 with stdlib unittest
    from unittest import defaultTestLoader, TestSuite


from fabric.api import run, put


def flatten_tests(test, accum):
    if type(test) == TestSuite:
        for t in test:
            flatten_tests(t, accum)
    else:
        accum.append(test)


def populate_django_users_for_fts(*builder_ids):
    create_user_script_handle, create_user_script_name = tempfile.mkstemp(".py")
    os.close(create_user_script_handle)

    create_user_script = open(create_user_script_name, "w")
    create_user_script.write("from dirigible.user.models import User\n")

    create_user_script.write(dedent("""
        for user in User.objects.all():
            if user.username != "admin":
                user.delete()
            else:
                profile = user.get_profile()
                profile.has_seen_sheet_page = True
                profile.save()
    """))

    suite = defaultTestLoader.discover(os.path.dirname(__file__))
    all_tests = []
    flatten_tests(suite, all_tests)
    for test in all_tests:
        if 'ModuleImportFailure' in str(test):
            getattr(test, test._testMethodName)()
        if not hasattr(test, 'user_count') or test.user_count == 0:
            continue
        for builder_id in builder_ids:
            for username in test.get_my_usernames(username_prefix=builder_id):
                create_user_script.write("user = User(username='%s')\n" % (username))
                create_user_script.write("user.set_password('p4ssw0rd')\n")
                create_user_script.write("user.save()\n")
                create_user_script.write("profile = user.get_profile()\n")
                create_user_script.write("profile.has_seen_sheet_page = True\n")
                create_user_script.write("profile.save()\n")

    create_user_script.close()
    put(create_user_script_name, '/home/dirigible/python/dirigible/create_ft_users.py')
    run("PYTHONPATH=/home/dirigible/python DJANGO_SETTINGS_MODULE=dirigible.settings python /home/dirigible/python/dirigible/create_ft_users.py")
