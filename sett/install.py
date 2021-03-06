#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse

from paver.easy import task, consume_nargs, needs, sh, cmdopts, path
from sett import which


@task
@needs(['scp'])
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
def remote_install(args, options, env):
    """Build, copy to a remote SSH and install in the given venv"""

    remote = args[0]
    venv = path(options.remote_install.venv)

    target = env.wheel_file.basename()
    ssh_command = [
        which.ssh,
        remote,
        '-C',
        venv.joinpath('bin/pip'), 'install', target,
    ]
    if options.remote_install.force:
        ssh_command.extend(['--no-deps', '--upgrade'])
    sh(ssh_command)
    sh([which.ssh, remote, '-C', 'rm', target])


@task
@needs(['wheel'])
@cmdopts([
    optparse.make_option('-f', '--force',
                         action='store_true',
                         default=False,
                         help='Force the installation',
                         ),
])
@consume_nargs(1)
def local_install(args, options, env):
    """Install the package in a virtual env present on the local filesystem"""
    target = env.wheel_file
    venv = path(args[0])

    pip_install = [venv.joinpath('bin/pip'), 'install', target]
    if options.local_install.force:
        pip_install.extend(['--no-deps', '--upgrade'])

    sh(pip_install)
