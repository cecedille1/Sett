#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from paver.easy import task, needs, cmdopts, sh, error, options, debug
from sett import which


# Errors codes:
# E10 Tab and spaces
# E11 Indentation
# E4 Imports
# E7 Statements
# E9 Errors

ERROR_CODES = {
    'E9',  # Syntax Error
    'F404',   # future import(s) name after other statements
    'F821',  # undefined name name
    'F823',  # local variable name ... referenced before assignment
    'F831',  # duplicate argument name in function definition
}

WARNING_CODES = {
    'E12', 'E13',  # Indentation of hanging brackets and paranthesis
    'E2',  # Whitespace between operators and brackets and paranthesis
    'E3',  # Blank lines
    'E402',  # Import at the wrong place
    'E5',  # Line length
    'W292', 'W391',  # \n at the end
    'W503',  # And or or at the line beginning
}


class CodesSet(object):
    def __init__(self, values):
        self.values = frozenset(values)

    def __repr__(self):
        return 'CodesSet({{{}}})'.format(', '.join(repr(x) for x in self.values))

    def __contains__(self, code):
        return any(code[0:x + 1] in self.values
                   for x in range(len(code)))


class QualityChecker(object):
    def __init__(self, warning_codes=None, error_codes=None):
        self.warning_codes = CodesSet(warning_codes) or frozenset()
        self.error_codes = CodesSet(error_codes) or frozenset()

    def __call__(self):
        packages = [package for package in options.setup['packages'] if '.' not in package]
        report = self.call_flake8(packages)
        codes = self.get_codes(report)
        return QualityReport(report,
                             has_errors=any(c in self.error_codes for c in codes),
                             has_failures=any(c not in self.warning_codes for c in codes),
                             has_warnings=any(c in self.warning_codes for c in codes),
                             )

    def call_flake8(self, packages):
        flake8_command = [which.flake8, '--exit-zero']
        flake8_command.extend(packages)
        return sh(flake8_command, capture=True)

    def get_codes(self, report):
        codes = set()
        for line in report.split('\n'):
            if not line:
                continue
            code = line.split(':', 3)[-1].strip().split()[0]
            codes.add(code)
        return codes


class QualityReport(object):
    """
    Quality Report contains the raw result of the report from flake8 and
    boolean values corresponding to the level of failure.

    The report is falsy if it does not contains any error. Then warning,
    failure, and errors respectively show if the report contains simple
    *warnings* that should not invalidate the quality, substantial *failures*
    that should invalidate the quality but still let the tests run and critical
    *errors* that prevent the process from continuing.
    """
    def __init__(self, text_report, has_errors, has_warnings, has_failures):
        self.text_report = text_report
        self.has_warnings = has_warnings
        self.has_errors = has_errors
        self.has_failures = has_failures

    @property
    def level(self):
        if not self:
            return 0
        if self.has_errors:
            return 3
        if self.has_failures:
            return 2
        if self.has_warnings:
            return 1

    def __bool__(self):
        return bool(self.text_report)

    __nonzero__ = __bool__

    def write(self, outfile):
        outfile.write(self.text_report)

    def __repr__(self):
        if not self:
            return '<Report good>'
        if self.has_errors:
            return '<Report errors>'
        if self.has_failures:
            return '<Report failed>'
        if self.has_warnings:
            return '<Report warning>'


@task
@needs(['setup_options'])
@cmdopts([
    ('output=', 'o', 'Output of the flake8 report'),
    ('stricness', 's', 'Strictness of the report, 1=warning, [2=failures], 3=errors'),
])
def quality(options):
    """Enforces PEP8"""
    qc = QualityChecker(WARNING_CODES, ERROR_CODES)
    report = qc()
    debug('Report is %s', report)

    out = getattr(options, 'output', '-')
    if out == '-':
        outfile = sys.stdout
    else:
        outfile = open(out, 'w')
    try:
        report.write(outfile)
    finally:
        if outfile is not sys.stdout:
            outfile.close()

    if not report:
        return False

    if report.has_errors:
        error('Critical errors in quality check')
    elif report.has_failures:
        error('Errors in quality check')
    elif report.has_warnings:
        error('Warnings in quality check')

    strictness = int(getattr(options, 'strictness', 2))
    if report.level >= strictness:
        raise SystemExit(1)
