#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from paver.easy import task, needs, cmdopts, sh, error
from sett import which


WARNING_CODES = {
    'E12', 'E13',  # Indentation of hanging brackets and paranthesis
    'E2',  # Whitespace between operators and brackets and paranthesis
    'E3',  # Blank lines
    'E402',  # Import at the wrong place
    'E5',  # Line length
    'W292', 'W391',  # \n at the end
    'W503',  # And or or at the line beginning
}
# Errors codes:
# E10 Tab and spaces
# E11 Indentation
# E4 Imports
# E7 Statements
# E9 Errors


@task
@needs(['setup_options'])
@cmdopts([
    ('output=', 'o', 'Output of the flake8 report'),
])
def quality(options):
    """Enforces PEP8"""
    out = getattr(options, 'output', '-')
    flake8_command = [which.flake8, '--exit-zero']
    flake8_command.extend(package for package in options.setup['packages'] if '.' not in package)
    flake8_report = sh(flake8_command, capture=True)

    codes = set()
    for line in flake8_report.split('\n'):
        if not line:
            continue
        code = line.split(':')[-1].strip().split()[0]
        codes.add(code)

    if out == '-':
        outfile = sys.stdout
    else:
        outfile = open(out, 'w')

    try:
        outfile.write(flake8_report)
    finally:
        if outfile is not sys.stdout:
            outfile.close()

    if not codes:
        return

    for code in codes:
        for x in range(len(code)):
            if code[0:x + 1] in WARNING_CODES:
                break
        else:
            error('Failure of quality check')
            raise SystemExit(1)
