#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
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


class FileReplacer(object):
    """
    File replacing utility. It replaces the source_path by the target_path and
    reverts the modification on exit. It is usable as a context manager or as a
    function decorator.

    >>> @task
    >>> @FileReplacer('requirements_minimal.txt', 'requirements.txt')
    >>> def make_minimal():
    ...     call_task('make')

    >>> @task
    >>> def make():
    ...     with FileReplacer('settings_prod.py', 'settings.py'):
    ...         return call_task('django', 'dumpdata')
    """

    def __init__(self, source_path, target_path):
        self.source_path = path(source_path)
        self.target_path = path(target_path)
        self.temp_path = self.target_path.dirname().joinpath('.-' + self.target_path.basename())
        self.target_path_exists = self.target_path.exists()

    def __call__(self, fn):
        """Decorates the fn with the FileReplacer instance"""
        @functools.wraps(fn)
        def inner(*args, **kw):
            with self:
                return fn(*args, **kw)
        return inner

    def __enter__(self):
        if self.target_path_exists:
            self.target_path.move(self.temp_path)

        self.source_path.move(self.target_path)
        return self

    def __exit__(self, exc_value, exc_type, tb):
        self.target_path.move(self.source_path)
        if self.target_path_exists:
            self.temp_path.move(self.target_path)
