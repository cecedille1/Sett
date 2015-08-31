#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse

from paver.easy import task, call_task, consume_nargs, needs, sh, cmdopts, path


@task
@needs('scp')
@consume_nargs(1)
@cmdopts([
    optparse.make_option('-V', '--venv',
                         default='venv',
                         help='virtual env on the remote host',
                         ),
    optparse.make_option('-f', '--force',
                         action='store_true',
                         default=False,
                         help='Force the installation',
                         ),
])
def remote_install(args, options):
    """Build, copy to a remote SSH and install in the given venv"""

    remote = args[0]
    venv = path(options.remote_install.venv)

    target = '{name}-{version}.tar.gz'.format(**options.setup)
    ssh_command = [
        'ssh', remote,
        '-C',
        venv.joinpath('bin/pip'), 'install', target,
    ]
    if options.remote_install.force:
        ssh_command.extend(['--no-deps', '--upgrade'])
    sh(ssh_command)
    sh(['ssh', remote, '-C', 'rm', target])


@task
@needs(['setup_options'])
@cmdopts([
    optparse.make_option('-f', '--force',
                         action='store_true',
                         default=False,
                         help='Force the installation',
                         ),
])
@consume_nargs(1)
def local_install(args, options):
    """Install the package in a virtual env present on the local filesystem"""
    call_task('sdist')
    target = 'dist/{name}-{version}.tar.gz'.format(**options.setup)
    venv = path(args[0])

    pip_install = [venv.joinpath('bin/pip'), 'install', target]
    if options.local_install.force:
        pip_install.extend(['--no-deps', '--upgrade'])

    sh(pip_install)
