#!/usr/bin/env python
# -*- coding: utf-8 -*-


from paver.easy import task, consume_args, call_task, sh
from sett import which


@task
@consume_args
def git_copy(args):
    call_task('git', ['clone', '--depth', '1'] + args)


@task
@consume_args
def git(args):
    sh([which.git] + args)
