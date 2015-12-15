#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, consume_nargs, needs, sh

from sett.bin import which


@task
@needs(['wheel'])
@consume_nargs(1)
def scp(args, options, env):
    """Build and copy to a remote SSH"""
    remote, = args
    if ':' not in remote:
        remote += ':'
    sh([which.scp, env.wheel_file, remote])
