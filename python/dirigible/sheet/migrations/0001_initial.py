# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Clipboard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contents_json', models.TextField(default=b'{}')),
                ('is_cut', models.BooleanField(default=False)),
                ('source_left', models.IntegerField(null=True)),
                ('source_top', models.IntegerField(null=True)),
                ('source_right', models.IntegerField(null=True)),
                ('source_bottom', models.IntegerField(null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sheet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('version', models.IntegerField(default=0)),
                ('name', models.TextField(default=b'Untitled')),
                ('width', models.IntegerField(default=52)),
                ('height', models.IntegerField(default=1000)),
                ('contents_json', models.TextField(default=b'{ "_console_text": "", "_usercode_error": null  }')),
                ('timeout_seconds', models.IntegerField(default=55)),
                ('is_public', models.BooleanField(default=False)),
                ('allow_json_api_access', models.BooleanField(default=False)),
                ('api_key', models.CharField(max_length=72)),
                ('column_widths_json', models.TextField(default=b'{}')),
                ('usercode', models.TextField(default=b'\nload_constants(worksheet)\n\n# Put code here if it needs to access constants in the spreadsheet\n# and to be accessed by the formulae.  Examples: imports,\n# user-defined functions and classes you want to use in cells.\n\nevaluate_formulae(worksheet)\n\n# Put code here if it needs to access the results of the formulae.\n')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='clipboard',
            name='source_sheet',
            field=models.ForeignKey(to='sheet.Sheet', null=True),
            preserve_default=True,
        ),
    ]
