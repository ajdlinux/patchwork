# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephenfinucane@hotmail.com>
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

import os

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from patchwork.tests import TEST_MAIL_DIR


class ParsemailTest(TestCase):
    def test_invalid_path(self):
        with self.assertRaises(IOError):
            call_command('parsemail', 'xyz123random')

    def test_path_failure(self):
        # we haven't created a project yet, so this will fail
        with self.assertRaises(SystemExit) as exc:
            call_command('parsemail',
                         os.path.join(TEST_MAIL_DIR,
                                      '0001-git-pull-request.mbox'))

        self.assertEqual(exc.exception.code, 1)

    def test_stdin_failure(self):
        # we haven't created a project yet, so this will fail
        with open(os.path.join(TEST_MAIL_DIR,
                               '0001-git-pull-request.mbox')) as file_:
            with self.assertRaises(SystemExit) as exc:
                call_command('parsemail',
                             stdin=file_)

            self.assertEqual(exc.exception.code, 1)


class ParsearchiveTest(TestCase):
    def test_invalid_path(self):
        out = StringIO()
        with self.assertRaises(SystemExit) as exc:
            call_command('parsearchive', 'xyz123random', stdout=out)
        self.assertEqual(exc.exception.code, 1)

    def test_invalid_mbox(self):
        out = StringIO()
        # we haven't created a project yet, so this will fail
        call_command('parsearchive',
                     os.path.join(TEST_MAIL_DIR,
                                  '0001-git-pull-request.mbox'),
                     stdout=out)

        self.assertIn('Processed 1 messages -->', out.getvalue())
        self.assertIn('  1 dropped', out.getvalue())
