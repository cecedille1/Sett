#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, path, consume_args


@task
@consume_args
def clean_pyc(args):
    for dir in args:
        for file in path(dir).walkfiles('*.pyc'):
            path(file).unlink()
