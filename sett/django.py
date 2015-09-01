#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import re
import itertools
import subprocess
import collections

from paver.easy import (task, consume_nargs, consume_args, might_call,
                        call_task, sh, no_help, info, needs, debug, path,
                        environment)

from sett.paths import ROOT
from sett.bin import which


@task
def clean_migrations():
    """
    Merge uncommitted migrations
    """
    migration_re = re.compile('^\d{4}_[a-z0-9_]+\.py$')
    git_status = subprocess.Popen([
        which.git, 'ls-files', '--others', '--exclude-standard',
    ],
        stdout=subprocess.PIPE,
    )
    encoding = sys.getfilesystemencoding()
    matches = collections.defaultdict(list)
    for line in git_status.stdout:
        file_path = path(line.strip().decode(encoding))
        if '/migrations/' in file_path and migration_re.match(file_path.basename()):
            matches[file_path.splitall()[1]].append(file_path)
    git_status.wait()

    for app_label, scripts in matches.items():
        if len(scripts) <= 1:
            scripts.clear()

    if not any(matches.values()):
        debug('No uncommited migration to merge')

    for scripts in matches.values():
        for script in scripts:
            script.remove()

    if not environment.dry_run:
        args = ['makemigrations']
        args.extend(m for m in matches if matches[m])
        call_task('django', args=args)


@task
@no_help
def django_settings():
    import django
    django.setup()


@task
@needs('django_settings')
@consume_nargs(1)
def django_cmd(args):
    """Run a django management command"""
    from django.core.management import call_command
    call_command(args[0],)


@task
@needs('django_settings')
@consume_args
def django(args):
    """Run a django management command with arguments"""
    if not args:
        args = ['--help']
    elif args[0] == 'runserver':
        return call_task('_runserver', args=['8000'])

    from django.core.management import execute_from_command_line
    command = ['django']
    command.extend(args)
    execute_from_command_line(command)


@task
@might_call('django')
@consume_nargs(1)
def start_app(args):
    name = args[0]
    call_task('django', args=['start_app', name, ROOT])
    call_task('add_installed_app', args=[name])


@task
@consume_nargs(1)
@needs('django_settings')
def add_installed_app(args):
    name = args[0]

    from django.conf import settings
    if name in settings.INSTALLED_APPS:
        info('App %s is already in INSTALLED_APPS', name)
        return

    settings_path = ROOT.joinpath('magellan', 'settings.py')
    debug('Install app in %s', settings_path)

    with open(settings_path, 'r+') as settings:
        settings_lines = settings.readlines()
        lines_iterator = enumerate(settings_lines, start=1)
        for line_no, line in lines_iterator:
            if line.startswith('INSTALLED_APPS'):
                debug('Found INSTALLED_APPS at %s', line_no)
                break
        else:
            debug('Did not found INSTALLED_APPS')
            return

        for line_no, line in lines_iterator:
            code = line.split('#', 1)[0]
            if ']' in code or ')' in code:
                debug('Found last segment at %s', line_no)
                break
        else:
            debug('Did not found list ending')
            return

        # Copy the indent of the last line
        indent = ''.join(itertools.takewhile(str.isspace, settings_lines[line_no - 2]))

        settings_lines.insert(line_no - 1, '{}\'{}\',\n'.format(indent, name))

        settings.seek(0)
        settings.writelines(settings_lines)


@task
@might_call('django')
def django_db():
    """alias for `django makemigrations django migrate`"""
    call_task('django_cmd', args=['makemigrations'])
    call_task('django_cmd', args=['migrate'])


@task
@consume_args
def runserver(args):
    """Run the dev server for django"""
    info('Forking')
    command = [
        sys.executable,
        sys.argv[0],
        'sett.django._runserver',
    ]
    command.extend(args)
    sh(command)


@task
@no_help
@consume_args
def _runserver(args):
    from django.core.management import execute_from_command_line
    command = ['_runserver', 'runserver']
    command.extend(args)
    info('Forked')
    execute_from_command_line(command)


@task
def statics():
    """
    Collect the static files
    """
    ignore_list = [
        'config.rb',
        '*.scss',
    ]

    args = ['collectstatic', '--noinput']
    for ignore in ignore_list:
        args.extend(['-i', ignore])

    call_task('django', args=args)