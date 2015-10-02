#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os

from paver.easy import debug, task, consume_args, call_task, info, environment

from sett import ROOT, which, defaults
from sett.gem import GEM_HOME


def run_compass(*commands, **kw):
    command = [which.compass]
    command.extend(commands)
    command.append(ROOT.joinpath(getattr(environment, 'compass_root', defaults.COMPASS_DIR)))

    info('Running: %s', ' '.join(command))
    env = dict(os.environ)
    env['GEM_HOME'] = GEM_HOME
    compass = subprocess.Popen(command, env=env)
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
