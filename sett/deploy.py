#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import optparse

from paver.easy import task, needs, sh, call_task, cmdopts, consume_nargs


@task
@needs(['setup_options'])
@consume_nargs(1)
def scp(args, options):
    """Build and copy to a remote SSH"""
    call_task('sdist')
    target = 'dist/{name}-{version}.tar.gz'.format(**options.setup)

    remote, = args
    if ':' not in remote:
        remote += ':'
    sh(['scp', target, remote])


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
    venv = options.remote_install.venv

    target = '{name}-{version}.tar.gz'.format(**options.setup)
    ssh_command = [
        'ssh', remote,
        '-C',
        os.path.join(venv, 'bin', 'pip'), 'install', target,
    ]
    if options.remote_install.force:
        ssh_command.extend(['--no-deps', '--upgrade'])
    sh(ssh_command)
    sh(['ssh', remote, '-C', 'rm', target])


@task
@needs(['setup_options'])
def push():
    """Pushes the archive in the enix repo"""
    call_task('sdist')
    call_task('upload', options={
        'repository': 'http://enixpi.enix.org',
    })
