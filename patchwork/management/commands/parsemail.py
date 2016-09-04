# Patchwork - automated patch tracking system
# Copyright (C) 2016 Intel Corporation
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

import argparse
from email import message_from_file
import logging
from optparse import make_option
import sys

import django
from django.core.management import base

from patchwork.parser import parse_mail

logger = logging.getLogger(__name__)


class Command(base.BaseCommand):
    help = 'Parse an mbox file and store any patch/comment found.'

    if django.VERSION < (1, 8):
        args = '<infile>'
        option_list = base.BaseCommand.option_list + (
            make_option(
                '--list-id',
                help='mailing list ID. If not supplied, this will be '
                'extracted from the mail headers.'),
        )
    else:
        def add_arguments(self, parser):
            parser.add_argument(
                'infile',
                nargs='?',
                type=argparse.FileType('r'),
                default=sys.stdin,
                help='input mbox file (a filename or stdin)')
            parser.add_argument(
                '--list-id',
                action='store_true',
                help='mailing list ID. If not supplied, this will be '
                'extracted from the mail headers.')

    def handle(self, *args, **options):
        path = (args[0] if args else
                options['infile'] if 'infile' in options else None)
        stdin = options.get('stdin', sys.stdin)

        # Attempt to parse the path if provided, and fallback to stdin if not
        if path and not isinstance(path, file):
            logger.info('Parsing mail loaded by filename')
            with open(path, 'r+') as file_:
                mail = message_from_file(file_)
        else:
            logger.info('Parsing mail loaded from stdin')
            mail = message_from_file(stdin)

        try:
            result = parse_mail(mail, options['list_id'])
            if result:
                sys.exit(0)
            logger.warning('Failed to parse mail')
            sys.exit(1)
        except Exception:
            logger.exception('Error when parsing incoming email',
                             extra={'mail': mail.as_string()})
