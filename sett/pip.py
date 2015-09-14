#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

from paver.easy import consume_args, consume_nargs, task, sh, call_task, path, info
from sett import ROOT, defaults


VENV_BIN = path(sys.executable).dirname()
VENV_DIR = VENV_BIN.dirname()


REQUIREMENTS = ROOT.joinpath(defaults.REQUIREMENTS)


@task
@consume_args
def pip(args):
    """Run a pip command"""
    pip_bin = VENV_BIN.joinpath('pip')
    sh([pip_bin] + args)


@task
@consume_args
def pip_install(args, options):
    """Install a pip package"""
    command = ['install']
    if defaults.PYPI_PACKAGE_INDEX:
        command.extend(['--index-url', defaults.PYPI_PACKAGE_INDEX])
        if defaults.PYPI_PACKAGE_INDEX_IGNORE_SSL:
            try:
                from urlparse import urlparse
            except ImportError:
                from urllib.parse import urlparse

            url = urlparse(defaults.PYPI_PACKAGE_INDEX)
            command.extend(['--trusted-host', url.netloc])

    command.extend(args)
    call_task('pip', args=command)


@task
def pip_setup():
    """Install the requirements.txt"""
    call_task('pip_install', args=['-r', REQUIREMENTS])


@task
@consume_nargs(1)
def pip_req(args):
    """Install a pip package and add it to the requirements.txt"""
    package = args[0]
    call_task('pip_install', [package])

    info('Adding %s to requirements.txt', package)
    with open(REQUIREMENTS, 'a') as req_txt:
        req_txt.write('{}\n'.format(package))
