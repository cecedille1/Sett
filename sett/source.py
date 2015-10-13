#!/usr/bin/env python
# -*- coding: utf-8 -*-

from paver.easy import task, path, needs, consume_nargs


@task
@needs(['setup_options'])
def clean_pyc(options):
    for dir in options.setup['packages']:
        for file in path(dir).walkfiles('*.pyc', errors='ignore'):
            path(file).unlink()


@task
@consume_nargs(1)
def packagize(args):
    filename, = args
    filename = path(filename)

    module_root, py = filename.splitext()
    module_root.mkdir()
    filename.rename(module_root.joinpath('__init__.py'))
