#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys

from paver.easy import consume_args, consume_nargs, task, sh, call_task, path, info
from sett import ROOT, defaults, which
from sett.utils import BaseInstalledPackages

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


class NotAPath(object):
    def exists(self):
        return False


VENV_DIR = path(sys.prefix)

if hasattr(sys, 'real_prefix'):
    VENV_BIN = VENV_DIR.joinpath('bin')
else:
    VENV_BIN = NotAPath()


class InstalledPackages(BaseInstalledPackages):
    def __contains__(self, gem):
        if ':' in gem:
            gem, version = gem.split(':', 1)
        return super(InstalledPackages, self).__contains__(gem)

    def evaluate(self):
        from pip.utils import get_installed_distributions
        return [i.project_name for i in get_installed_distributions()]

installed_packages = InstalledPackages()


@task
@consume_args
def pip(args):
    """Run a pip command"""
    if not args:
        args = ['freeze']
    elif args[0] == 'freeze' and len(args) > 1:
        out = sh([which.pip, 'freeze'], capture=True)
        keys = tuple(l.lower() for l in args[1:])
        for line in out.split():
            if line.lower().startswith(keys):
                sys.stdout.write(line)
                sys.stdout.write('\n')
        return
    elif args[0] == 'install':
        if defaults.PYPI_PACKAGE_INDEX:
            extra = ['--index-url', defaults.PYPI_PACKAGE_INDEX]
            if defaults.PYPI_PACKAGE_INDEX_IGNORE_SSL:
                url = urlparse(defaults.PYPI_PACKAGE_INDEX)
                extra.extend(['--trusted-host', url.netloc])
        args[1:1] = extra

    sh([which.pip] + args)
    which.update()


@task
@consume_args
def pip_install(args, options):
    """Install a pip package"""
    call_task('pip', args=['install'] + args)


@task
def pip_setup():
    """Install the requirements.txt"""
    requirements = ROOT.joinpath(defaults.REQUIREMENTS)
    call_task('pip_install', args=['-r', requirements])


@task
@consume_nargs(1)
def pip_req(args):
    """Install a pip package and add it to the requirements.txt"""
    package = args[0]
    call_task('pip_install', [package])

    requirements = ROOT.joinpath(defaults.REQUIREMENTS)
    with open(requirements, 'r+') as req_txt:
        for line in req_txt:
            if line.strip() == package:
                info('%s already present in %s', package, requirements)
                break
        else:
            info('Adding %s to %s', package, requirements)
            req_txt.write('{}\n'.format(package))
