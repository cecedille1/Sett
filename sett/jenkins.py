#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, call_task


@task
def jenkins():
    """Runs the Jenkins tasks"""
    # Generate nosetest.xml
    # Generate coverage.xml
    # Generate flake8.log

    try:
        call_task('quality', options={
            'output': 'flake8.log',
            'strictness': 2,
        })
    except SystemExit:
        quality_ok = False
    else:
        quality_ok = True

    call_task('coverage', options={
        'xunit': 'nosetests.xml',
        'xcoverage': 'coverage.xml',
    })
    if not quality_ok:
        raise SystemExit(1)
