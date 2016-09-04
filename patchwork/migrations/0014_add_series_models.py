# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patchwork', '0013_slug_check_context'),
    ]

    operations = [
        migrations.CreateModel(
            name='Series',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'verbose_name_plural': 'Series',
            },
        ),
        migrations.CreateModel(
            name='SeriesReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('msgid', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SeriesRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField()),
                ('version', models.IntegerField(default=1, help_text=b'Version of series revision as indicated by the subject prefix(es)')),
                ('total', models.IntegerField(help_text=b'Number of patches in series as indicated by the subject prefix(es)')),
                ('group', models.ForeignKey(related_query_name=b'revision', related_name='revisions', blank=True, to='patchwork.Series', null=True)),
                ('submitter', models.ForeignKey(to='patchwork.Person')),
            ],
        ),
        migrations.AddField(
            model_name='seriesreference',
            name='series',
            field=models.ForeignKey(related_query_name=b'reference', related_name='references', to='patchwork.SeriesRevision'),
        ),
        migrations.AddField(
            model_name='coverletter',
            name='series',
            field=models.OneToOneField(related_name='cover_letter', null=True, blank=True, to='patchwork.SeriesRevision'),
        ),
        migrations.AddField(
            model_name='patch',
            name='series',
            field=models.ForeignKey(related_query_name=b'patch', related_name='unique_patches', blank=True, to='patchwork.SeriesRevision', null=True),
        ),
    ]
