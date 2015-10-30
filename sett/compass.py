#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse
from paver.easy import task, consume_args, call_task, cmdopts, path

from sett import ROOT, which, defaults
from sett.gem import run_ruby


def get_compass_dir():
    return ROOT.joinpath(defaults.COMPASS_DIR)


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
    call_task('compass', args=['watch', get_compass_dir()])


@task
def compile():
    """Alias for compass compile"""
    call_task('compass', args=['compile', get_compass_dir()])


@task
@cmdopts([
    optparse.make_option('-o', '--output',
                         default='',
                         help='Output a checkstyle report'),
])
def scss_quality(options):
    if options.scss_quality.output:
        extra = [
            '--require', 'scss_lint_reporter_checkstyle',
            '--format', 'Checkstyle',
            '--out', options.output,
        ]
    else:
        extra = []

    if path(defaults.SCSS_LINT_CONFIG).exists():
        extra.extend(['--config', defaults.SCSS_LINT_CONFIG])

    run_ruby('scss-lint', get_compass_dir(), *extra, expect={0, 1})
