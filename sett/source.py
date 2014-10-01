#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, path, needs


@task
@needs(['setup_options'])
def clean_pyc(options):
    for dir in options.setup['packages']:
        for file in path(dir).walkfiles('*.pyc', errors='ignore'):
            path(file).unlink()
