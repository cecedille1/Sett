#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from paver.easy import task, needs, cmdopts, sh
from sett import which, defaults


@task
@needs(['setup_options'])
@cmdopts([
    ('output=', 'o', 'Output of the flake8 report'),
])
def flake8(options):
    """Enforces PEP8"""
    out = getattr(options.flake8, 'output', '-')
    flake8_command = [which.flake8]
    flake8_command.extend(defaults.FLAKE8_EXTRA_ARGS)
    flake8_command.extend(package for package in options.setup['packages'] if '.' not in package)
    flake8_report = sh(flake8_command, capture=True)

    if out == '-':
        outfile = sys.stdout
    else:
        outfile = open(out, 'wb')

    try:
        outfile.write(flake8_report)
    finally:
        if outfile is not sys.stdout:
            outfile.close()
