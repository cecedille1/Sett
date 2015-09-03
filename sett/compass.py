#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from paver.easy import debug, task, consume_args, call_task, info, environment

from sett.paths import ROOT
from sett.gem import GEM_HOME
from sett.bin import which


def run_compass(*commands, **kw):
    command = [which.compass]
    command.extend(commands)
    command.append(ROOT.joinpath(getattr(environment, 'compass_root', 'compass')))

    info('Running: %s', ' '.join(command))
    compass = subprocess.Popen(command, env={
        'GEM_HOME': GEM_HOME,
    })
    if not kw.get('background', False):
        rc = compass.wait()
        debug('compass returned %s', rc)
    return compass


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
