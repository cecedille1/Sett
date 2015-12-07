#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os


from paver.easy import task, call_task, environment, path, no_help, needs, debug, info
from paver.setuputils import setup, _get_distribution

from sett import ROOT, optional_import

version = optional_import('packaging.version')


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
@needs(['setup_options', 'wheel'])
def make(options):
    """Overrides sdist to make sure that our setup.py is generated."""
    call_task('sdist', options={'formats': ['gztar', 'zip']})

    if not version.Version(options.setup.version).is_prerelease:
        call_task('link_latest')


@task
@needs(['setup_options'])
def wheel():
    call_task('bdist_wheel')

    dist = _get_distribution()
    for cmd, x, file in dist.dist_files:
        if cmd == 'bdist_wheel':
            environment.wheel_file = path(file).abspath()
            debug('Invented the wheel in %s', environment.wheel_file)
            break
    else:
        info('Cannot invent the wheel')


@task
@needs(['setup_options'])
def link_latest():
    dist = _get_distribution()
    name = dist.get_name()
    prefix = len(dist.get_fullname()) + 1

    for cmd, x, file in dist.dist_files:
        file = path(file)
        ext = file.basename()[prefix:]
        link = ROOT.joinpath('dist/{}-latest.{}'.format(name, ext))

        if link.islink():
            os.unlink(link)

        info('Link %s to %s', link, file.basename())
        file.basename().symlink(link)
