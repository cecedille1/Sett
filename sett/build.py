#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os

from packaging.version import Version

from paver.easy import task, call_task, path, no_help, needs
from paver.setuputils import setup

from sett import ROOT


@task
@no_help
def setup_options(options):
    try:
        from setup import build_info
    except ImportError:
        sys.path.append(ROOT)
        from setup import build_info
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

    if not Version(options.setup.version).is_prerelease:
        target = '{name}-{version}.tar.gz'.format(**options.setup)
        link = ROOT.joinpath('dist/{name}-latest.tar.gz'.format(**options.setup))

        if link.islink():
            os.unlink(link)

        sys.stderr.write('Link {0} to {1}\n'.format(link, target))
        path(target).symlink(link)
