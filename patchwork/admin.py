# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# This file is part of the Patchwork package.
#
# Patchwork is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Patchwork is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Patchwork; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from __future__ import absolute_import

from django.contrib import admin

from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import Comment
from patchwork.models import CoverLetter
from patchwork.models import DelegationRule
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import SeriesReference
from patchwork.models import SeriesRevision
from patchwork.models import State
from patchwork.models import Submission
from patchwork.models import Tag
from patchwork.models import UserProfile


class DelegationRuleInline(admin.TabularInline):
    model = DelegationRule
    fields = ('path', 'user', 'priority')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'linkname', 'listid', 'listemail')
    inlines = [
        DelegationRuleInline,
    ]
admin.site.register(Project, ProjectAdmin)


class PersonAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'has_account')
    search_fields = ('name', 'email')

    def has_account(self, person):
        return bool(person.user)

    has_account.boolean = True
    has_account.admin_order_field = 'user'
    has_account.short_description = 'Account'
admin.site.register(Person, PersonAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
admin.site.register(UserProfile, UserProfileAdmin)


class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_required')
admin.site.register(State, StateAdmin)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'date')
    list_filter = ('project', )
    search_fields = ('name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'
admin.site.register(Submission, SubmissionAdmin)


CoverLetterAdmin = SubmissionAdmin
admin.site.register(CoverLetter, CoverLetterAdmin)


class PatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'state', 'date',
                    'archived', 'is_pull_request', 'series')
    list_filter = ('project', 'state', 'archived', 'series')
    search_fields = ('name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'

    def is_pull_request(self, patch):
        return bool(patch.pull_url)

    is_pull_request.boolean = True
    is_pull_request.admin_order_field = 'pull_url'
    is_pull_request.short_description = 'Pull'
admin.site.register(Patch, PatchAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('submission', 'submitter', 'date')
    search_fields = ('submission__name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'
admin.site.register(Comment, CommentAdmin)


class CoverLetterInline(admin.StackedInline):
    model = CoverLetter
    extra = 0


class PatchInline(admin.StackedInline):
    model = Patch
    extra = 0


class SeriesRevisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'date', 'submitter', 'version', 'total',
                    'actual_total', 'complete')
    readonly_fields = ('actual_total', 'complete')
    search_fields = ('submitter_name', 'submitter_email')
    inlines = [CoverLetterInline, PatchInline]

    def complete(self, series):
        return series.complete
    complete.boolean = True
admin.site.register(SeriesRevision, SeriesRevisionAdmin)


class SeriesRevisionInline(admin.StackedInline):
    model = SeriesRevision
    readonly_fields = ('date', 'submitter', 'version', 'total',
                       'actual_total', 'complete')
    ordering = ('-date', )
    show_change_link = True
    extra = 0

    def complete(self, series):
        return series.complete
    complete.boolean = True


class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', )
    readonly_fields = ('name', )
    inlines = [SeriesRevisionInline]
admin.site.register(Series, SeriesAdmin)


class SeriesReferenceAdmin(admin.ModelAdmin):
    model = SeriesReference
admin.site.register(SeriesReference, SeriesReferenceAdmin)


class CheckAdmin(admin.ModelAdmin):
    list_display = ('patch', 'user', 'state', 'target_url',
                    'description', 'context')
    exclude = ('date', )
    search_fields = ('patch__name', 'project__name')
    date_hierarchy = 'date'
admin.site.register(Check, CheckAdmin)


class BundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'project', 'public')
    list_filter = ('public', 'project')
    search_fields = ('name', 'owner')
admin.site.register(Bundle, BundleAdmin)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(Tag, TagAdmin)
