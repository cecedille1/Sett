#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

from pip.util import is_prerelease

from paver.easy import task, call_task, path, no_help, needs
from paver.setuputils import setup


try:
    from setup import build_info
except ImportError:
    sys.path.append('.')
    from setup import build_info


@task
@no_help
def setup_options(options):
    setup(**build_info)


@task
def clean():
    """Clean the workspace"""
    path('dist').rmtree()


@task
@needs(['setup_options'])
def make(options):
    """Overrides sdist to make sure that our setup.py is generated."""
    call_task('sdist')

    if not is_prerelease(options.setup.version):
        target = '{name}-{version}.tar.gz'.format(**options.setup)
        link = 'dist/{name}-latest.tar.gz'.format(**options.setup)
        path(link).unlink_p()

        sys.stderr.write('Link {0} to {1}\n'.format(link, target))
        path(target).symlink(link)
