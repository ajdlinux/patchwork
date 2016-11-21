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

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.serializers import CharField
from rest_framework.serializers import HyperlinkedModelSerializer

from patchwork.api import PatchworkPermission
from patchwork.models import Project


class ProjectSerializer(HyperlinkedModelSerializer):
    # TODO(stephenfin): These should be renamed at the model layer
    link_name = CharField(max_length=255, source='linkname')
    list_id = CharField(max_length=255, source='listid')
    list_email = CharField(max_length=255, source='listemail')

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'link_name', 'list_id', 'list_email',
                  'web_url', 'scm_url', 'webscm_url')
        extra_kwargs = {
            'url': {'view_name': 'api-project-detail'},
        }


class ProjectMixin(object):

    permission_classes = (PatchworkPermission,)
    serializer_class = ProjectSerializer

    def get_queryset(self):
        query = Project.objects.all()

        if 'pk' in self.kwargs:
            try:
                query.get(id=int(self.kwargs['pk']))
            except (ValueError, Project.DoesNotExist):
                query.get(linkname=self.kwargs['pk'])

            # NOTE(stephenfin): We must do this to make sure the 'url'
            # field is populated correctly
            self.kwargs['pk'] = query[0].id

        return query


class ProjectList(ProjectMixin, ListAPIView):
    """List projects."""

    pass


class ProjectDetail(ProjectMixin, RetrieveUpdateAPIView):
    """Show a project."""

    pass
