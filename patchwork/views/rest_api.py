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

from django.conf import settings
from patchwork.models import Patch
from patchwork.rest_serializers import (
    ChecksSerializer, PatchSerializer, PersonSerializer, ProjectSerializer,
    UserSerializer, SeriesRevisionSerializer)

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.routers import NestedSimpleRouter


class LinkHeaderPagination(PageNumberPagination):
    """Provide pagination based on rfc5988 (how github does it)
       https://tools.ietf.org/html/rfc5988#section-5
       https://developer.github.com/guides/traversing-with-pagination
    """
    page_size = settings.REST_RESULTS_PER_PAGE
    page_size_query_param = 'per_page'

    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()

        link = ''
        if next_url is not None and previous_url is not None:
            link = '<{next_url}>; rel="next", <{previous_url}>; rel="prev"'
        elif next_url is not None:
            link = '<{next_url}>; rel="next"'
        elif previous_url is not None:
            link = '<{previous_url}>; rel="prev"'
        link = link.format(next_url=next_url, previous_url=previous_url)
        headers = {'Link': link} if link else {}
        return Response(data, headers=headers)


class PatchworkPermission(permissions.BasePermission):
    """This permission works for Project and Patch model objects"""
    def has_permission(self, request, view):
        if request.method in ('POST', 'DELETE'):
            return False
        return super(PatchworkPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # read only for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.is_editable(request.user)


class AuthenticatedReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        authenticated = request.user.is_authenticated()
        return authenticated and request.method in permissions.SAFE_METHODS


class PatchworkViewSet(ModelViewSet):
    pagination_class = LinkHeaderPagination

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.all()


class UserViewSet(PatchworkViewSet):
    permission_classes = (AuthenticatedReadOnly, )
    serializer_class = UserSerializer


class PeopleViewSet(PatchworkViewSet):
    permission_classes = (AuthenticatedReadOnly, )
    serializer_class = PersonSerializer

    def get_queryset(self):
        qs = super(PeopleViewSet, self).get_queryset()
        return qs.select_related('user__username')


class ProjectViewSet(PatchworkViewSet):
    permission_classes = (PatchworkPermission, )
    serializer_class = ProjectSerializer

    def _handle_linkname(self, pk):
        '''Make it easy for users to list by project-id or linkname'''
        qs = self.get_queryset()
        try:
            qs.get(id=pk)
        except (self.serializer_class.Meta.model.DoesNotExist, ValueError):
            # probably a non-numeric value which means we are going by linkname
            self.kwargs = {'linkname': pk}  # try and lookup by linkname
            self.lookup_field = 'linkname'

    def retrieve(self, request, pk=None):
        self._handle_linkname(pk)
        return super(ProjectViewSet, self).retrieve(request, pk)

    def partial_update(self, request, pk=None):
        self._handle_linkname(pk)
        return super(ProjectViewSet, self).partial_update(request, pk)


class PatchViewSet(PatchworkViewSet):
    permission_classes = (PatchworkPermission,)
    serializer_class = PatchSerializer

    def get_queryset(self):
        qs = super(PatchViewSet, self).get_queryset(
        ).prefetch_related(
            'check_set', 'patchtag_set'
        ).select_related('state', 'submitter', 'delegate')
        if 'pk' not in self.kwargs:
            # we are doing a listing, we don't need these fields
            qs = qs.defer('content', 'diff', 'headers')
        return qs

class SeriesRevisionViewSet(PatchworkViewSet):
    permission_classes = (PatchworkPermission,)
    serializer_class = SeriesRevisionSerializer

class CheckViewSet(PatchworkViewSet):
    serializer_class = ChecksSerializer

    def not_allowed(self, request, **kwargs):
        raise PermissionDenied()

    update = not_allowed
    partial_update = not_allowed
    destroy = not_allowed

    def create(self, request, patch_pk):
        p = Patch.objects.get(id=patch_pk)
        if not p.is_editable(request.user):
            raise PermissionDenied()
        request.patch = p
        return super(CheckViewSet, self).create(request)

    def list(self, request, patch_pk):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(patch=patch_pk)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


router = DefaultRouter()
router.register('patches', PatchViewSet, 'patch')
router.register('people', PeopleViewSet, 'person')
router.register('projects', ProjectViewSet, 'project')
router.register('users', UserViewSet, 'user')
router.register('seriesrevisions', SeriesRevisionViewSet, 'seriesrevision')

patches_router = NestedSimpleRouter(router, r'patches', lookup='patch')
patches_router.register(r'checks', CheckViewSet, base_name='patch-checks')
