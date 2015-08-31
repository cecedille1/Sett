#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, call_task, consume_nargs, needs, sh

from sett.bin import which


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
    sh([which.scp, target, remote])
