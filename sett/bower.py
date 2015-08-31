#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, consume_nargs, consume_args, sh, call_task

from sett.paths import ROOT
from sett.bin import which

NODE_MODULES = ROOT.joinpath('node_modules')


@task
@consume_args
def bower(args):
    """
    Runs a bower command
    """
    command = [
        which.node,
        NODE_MODULES.joinpath('bower/bin/bower'),
    ]
    command.extend(args)
    sh(command)


@task
@consume_nargs(1)
def bower_req(args):
    """
    Installs a bower package and save it
    """
    call_task('bower', args=['install', '--save', args[0]])
