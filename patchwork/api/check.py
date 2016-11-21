# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import CurrentUserDefault
from rest_framework.serializers import HiddenField
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.serializers import HyperlinkedIdentityField

from patchwork.api import MultipleFieldLookupMixin
from patchwork.models import Check
from patchwork.models import Patch


class CurrentPatchDefault(object):
    def set_context(self, serializer_field):
        self.patch = serializer_field.context['request'].patch

    def __call__(self):
        return self.patch


class CheckHyperlinkedIdentityField(HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if obj.pk is None:
            return None

        return self.reverse(
            view_name,
            kwargs={
                'patch_id': obj.patch.id,
                'check_id': obj.id,
            },
            request=request,
            format=format,
        )


class CheckSerializer(HyperlinkedModelSerializer):
    user = HyperlinkedRelatedField(
        'api-user-detail', read_only=True, default=CurrentUserDefault())
    patch = HiddenField(default=CurrentPatchDefault())
    url = CheckHyperlinkedIdentityField('api-check-detail')

    def run_validation(self, data):
        for val, label in Check.STATE_CHOICES:
            if label == data['state']:
                data['state'] = val
                break
        return super(CheckSerializer, self).run_validation(data)

    def to_representation(self, instance):
        data = super(CheckSerializer, self).to_representation(instance)
        data['state'] = instance.get_state_display()
        return data

    class Meta:
        model = Check
        fields = ('url', 'patch', 'user', 'date', 'state', 'target_url',
                  'context', 'description')
        read_only_fields = ('date',)
        extra_kwargs = {
            'url': {'view_name': 'api-check-detail'},
        }


class CheckMixin(object):

    queryset = Check.objects.prefetch_related('patch', 'user')
    serializer_class = CheckSerializer


class CheckListCreate(CheckMixin, ListCreateAPIView):
    """List or create checks."""

    lookup_url_kwarg = 'patch_id'

    def create(self, request, patch_id):
        p = Patch.objects.get(id=patch_id)
        if not p.is_editable(request.user):
            raise PermissionDenied()
        request.patch = p
        return super(CheckListCreate, self).create(request)


class CheckDetail(CheckMixin, MultipleFieldLookupMixin, RetrieveAPIView):
    """Show a check."""

    lookup_url_kwargs = ('patch_id', 'check_id')
    lookup_fields = ('patch_id', 'id')
