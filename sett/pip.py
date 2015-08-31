#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

from paver.easy import consume_args, consume_nargs, task, sh, call_task, path, info


VENV_BIN = path(sys.executable).dirname()
VENV_DIR = VENV_BIN.dirname()


@task
@consume_args
def pip(args):
    """Run a pip command"""
    pip_bin = VENV_BIN.joinpath('pip')
    command = [
        pip_bin,
    ]
    command.extend(args)
    sh(command)


@task
@consume_args
def pip_install(args):
    """Install a pip package"""
    command = [
        'install',
        '--cert',
        path(__file__).dirname().joinpath('enix.ca'),
    ]
    command.extend(args)
    call_task('pip', args=command)


@task
def pip_setup():
    """Install the requirements.txt"""
    call_task('pip_install', args=['-r', 'requirements.txt'])


@task
@consume_nargs(1)
def pip_req(args):
    """Install a pip package and add it to the requirements.txt"""
    package = args[0]
    call_task('pip_install', [package])

    info('Adding %s to requirements.txt', package)
    with open('requirements.txt', 'a') as req_txt:
        req_txt.write('{}\n'.format(package))
