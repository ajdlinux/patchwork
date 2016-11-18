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

from email.utils import make_msgid
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse

from patchwork.models import Check
from patchwork.models import Project
from patchwork.tests.utils import create_check
from patchwork.tests.utils import create_maintainer
from patchwork.tests.utils import create_patch
from patchwork.tests.utils import create_person
from patchwork.tests.utils import create_project
from patchwork.tests.utils import create_state
from patchwork.tests.utils import create_user

if settings.ENABLE_REST_API:
    from rest_framework import status
    from rest_framework.test import APITestCase
else:
    # stub out APITestCase
    from django.test import TestCase
    APITestCase = TestCase  # noqa


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestProjectAPI(APITestCase):

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-project-list')
        return reverse('api-project-detail', args=[item])

    def test_list(self):
        """Validate we can list the default test project."""
        project = create_project()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        proj = resp.data[0]
        self.assertEqual(project.linkname, proj['link_name'])
        self.assertEqual(project.name, proj['name'])
        self.assertEqual(project.listid, proj['list_id'])

    def test_detail(self):
        """Validate we can get a specific project."""
        project = create_project()

        resp = self.client.get(self.api_url(project.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(project.name, resp.data['name'])

        # make sure we can look up by linkname
        resp = self.client.get(self.api_url(resp.data['link_name']))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(project.name, resp.data['name'])

    def test_get_numeric_linkname(self):
        """Validate we try to do the right thing for numeric linkname"""
        project = create_project(linkname='12345')

        resp = self.client.get(self.api_url('12345'))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(project.name, resp.data['name'])

    def test_create(self):
        """Ensure creations are rejected."""
        project = create_project()
        data = {'linkname': 'l', 'name': 'n', 'listid': 'l', 'listemail': 'e'}

        # an anonymous user
        resp = self.client.post(self.api_url(), data)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # a superuser
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), data)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_update(self):
        """Ensure updates can be performed by maintainers."""
        project = create_project()
        data = {'linkname': 'TEST'}

        # an anonymous user
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # a normal user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # a maintainer
        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(project.id), data)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

    def test_delete(self):
        """Ensure deletions are rejected."""
        project = create_project()

        # an anonymous user
        resp = self.client.delete(self.api_url(project.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # a super user
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.delete(self.api_url(project.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
        self.assertEqual(1, Project.objects.all().count())


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPersonAPI(APITestCase):

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-person-list')
        return reverse('api-person-detail', args=[item])

    def test_list(self):
        """This API requires authenticated users."""
        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(user.username, resp.data[0]['name'])
        self.assertEqual(user.email, resp.data[0]['email'])
        self.assertIn('users/%d/' % user.id, resp.data[0]['user'])

    def test_unlinked_user(self):
        person = create_person()
        user = create_user()
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(2, len(resp.data))
        self.assertEqual(person.name, resp.data[0]['name'])
        self.assertIsNone(resp.data[0]['user'])

    def test_create_update_delete(self):
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.post(self.api_url(), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.patch(self.api_url(user.id), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(user.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestUserAPI(APITestCase):

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-user-list')
        return reverse('api-user-detail', args=[item])

    def test_list(self):
        """This API requires authenticated users."""
        # anonymous users
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        self.assertEqual(user.username, resp.data[0]['username'])
        self.assertNotIn('password', resp.data[0])
        self.assertNotIn('is_superuser', resp.data[0])

    def test_create_delete(self):
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.delete(self.api_url(user.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.post(self.api_url(user.id), {'email': 'foo@f.com'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(user.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_update(self):
        user = create_maintainer()
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)

        resp = self.client.patch(self.api_url(user.id), {'first_name': 'Tan'})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestPatchAPI(APITestCase):
    fixtures = ['default_tags']

    @staticmethod
    def api_url(item=None):
        if item is None:
            return reverse('api-patch-list')
        return reverse('api-patch-detail', args=[item])

    def test_list(self):
        """Validate we can list a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        patch_obj = create_patch()

        # anonymous user
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertEqual(patch_obj.name, patch_rsp['name'])
        self.assertNotIn('content', patch_rsp)
        self.assertNotIn('headers', patch_rsp)
        self.assertNotIn('diff', patch_rsp)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        patch_rsp = resp.data[0]
        self.assertEqual(patch_obj.name, patch_rsp['name'])

    def test_detail(self):
        """Validate we can get a specific patch."""
        patch = create_patch()

        resp = self.client.get(self.api_url(patch.id))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(patch.name, resp.data['name'])
        self.assertIn(TestProjectAPI.api_url(patch.project.id),
                      resp.data['project'])
        self.assertEqual(patch.msgid, resp.data['msgid'])
        self.assertEqual(patch.diff, resp.data['diff'])
        self.assertIn(TestPersonAPI.api_url(patch.submitter.id),
                      resp.data['submitter'])
        self.assertEqual(patch.state.name, resp.data['state'])
        self.assertIn(patch.get_mbox_url(), resp.data['mbox'])

    def test_detail_tags(self):
        patch = create_patch(
            content='Reviewed-by: Test User <test@example.com>\n')
        resp = self.client.get(self.api_url(patch.id))
        tags = resp.data['tags']
        self.assertEqual(3, len(tags))
        self.assertEqual(1, tags['Reviewed-by'])

    def test_create(self):
        """Ensure creations are rejected."""
        project = create_project()
        patch = {
            'project': project,
            'submitter': create_person().id,
            'msgid': make_msgid(),
            'name': 'test-create-patch',
            'diff': 'patch diff',
        }

        # anonymous user
        resp = self.client.post(self.api_url(), patch)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # superuser
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), patch)
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

    def test_update(self):
        """Ensure updates can be performed by maintainers."""
        project = create_project()
        patch = create_patch(project=project)
        state = create_state()

        # anonymous user
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # authenticated user
        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

        # maintainer
        user = create_maintainer(project)
        self.client.force_authenticate(user=user)
        resp = self.client.patch(self.api_url(patch.id), {'state': state.name})
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

    def test_delete(self):
        """Ensure deletions are always rejected."""
        project = create_project()
        patch = create_patch(project=project)

        # anonymous user
        resp = self.client.delete(self.api_url(patch.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        # superuser
        user = create_maintainer(project)
        user.is_superuser = True
        user.save()
        self.client.force_authenticate(user=user)
        resp = self.client.delete(self.api_url(patch.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)


@unittest.skipUnless(settings.ENABLE_REST_API, 'requires ENABLE_REST_API')
class TestCheckAPI(APITestCase):
    fixtures = ['default_tags']

    def api_url(self, item=None):
        if item is None:
            return reverse('api-check-list', args=[self.patch.id])
        return reverse('api-check-detail', kwargs={
            'patch_id': self.patch.id, 'check_id': item.id})

    def setUp(self):
        super(TestCheckAPI, self).setUp()
        project = create_project()
        self.user = create_maintainer(project)
        self.patch = create_patch(project=project)

    def _create_check(self):
        values = {
            'patch': self.patch,
            'user': self.user,
        }
        return create_check(**values)

    def test_list(self):
        """Validate we can list checks on a patch."""
        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(0, len(resp.data))

        check_obj = self._create_check()

        resp = self.client.get(self.api_url())
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(1, len(resp.data))
        check_rsp = resp.data[0]
        self.assertEqual(check_obj.get_state_display(), check_rsp['state'])
        self.assertEqual(check_obj.target_url, check_rsp['target_url'])
        self.assertEqual(check_obj.context, check_rsp['context'])
        self.assertEqual(check_obj.description, check_rsp['description'])

    def test_detail(self):
        """Validate we can get a specific check."""
        check = self._create_check()
        resp = self.client.get(self.api_url(check))
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(check.target_url, resp.data['target_url'])

    def test_create(self):
        """Ensure creations can be performed by user of patch."""
        check = {
            'state': 'success',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        self.assertEqual(1, Check.objects.all().count())

        user = create_user()
        self.client.force_authenticate(user=user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

    def test_create_invalid(self):
        """Ensure we handle invalid check states."""
        check = {
            'state': 'this-is-not-a-valid-state',
            'target_url': 'http://t.co',
            'description': 'description',
            'context': 'context',
        }

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.api_url(), check)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        self.assertEqual(0, Check.objects.all().count())

    def test_update_delete(self):
        """Ensure updates and deletes aren't allowed"""
        check = self._create_check()
        self.user.is_superuser = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        resp = self.client.patch(self.api_url(check), {'target_url': 'fail'})
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

        resp = self.client.delete(self.api_url(check))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)
