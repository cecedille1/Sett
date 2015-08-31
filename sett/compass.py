#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from paver.easy import debug, task, consume_nargs, call_task, info

from sett.paths import ROOT
from sett.gem import GEM_HOME


def run_compass(command, background=False):
    command = [
        GEM_HOME.joinpath('bin/compass'),
        command,
        ROOT.joinpath('compass'),
    ]
    info('Running: %s', ' '.join(command))
    compass = subprocess.Popen(command, env={
        'GEM_HOME': GEM_HOME,
    })
    if not background:
        rc = compass.wait()
        debug('compass returned %s', rc)
    return compass


@task
@consume_nargs(1)
def compass(args, options):
    """Run a compass command"""
    run_compass(args[0])


@task
def watch():
    """Alias for compass watch"""
    call_task('compass', args=['watch'])


@task
def compile():
    """Alias for compass compile"""
    call_task('compass', args=['compile'])
