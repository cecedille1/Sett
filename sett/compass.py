#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse
from paver.easy import task, consume_args, call_task, cmdopts, path

from sett import ROOT, which, defaults
from sett.gem import run_ruby


def run_compass(*commands, **kw):
    return run_ruby(which.compass, *commands, **kw)


@task
@consume_args
def compass(args, options):
    """Run a compass command. The root of the compass environment is the value
    of paver.environment.compass_root and defaults to ROOT/compass"""
    run_compass(*args)


@task
def watch():
    """Alias for compass watch"""
    call_task('compass', args=['watch'])


@task
def compile():
    """Alias for compass compile"""
    call_task('compass', args=['compile'])
