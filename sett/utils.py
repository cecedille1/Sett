#!/usr/bin/env python
# -*- coding: utf-8 -*-

import heapq
import tempfile
import collections
import sys
from sett import which
from paver.easy import debug, path, call_task, pushd, sh
from paver.tasks import environment, Task


def task_name(name):
    """
    Set the name of the task

    >>> @task
    >>> @task_name('django')
    >>> def django_task():
    ...     pass
    >>> environment.get_task('django')
    """
    def decorator(fn):
        fn.__name__ = name
        return fn
    return decorator


class TaskAlternativeTaskFinder(object):
    def __init__(self, ta):
        self.ta = ta

    def get_tasks(self):
        return [Task(x) for x in self.ta]

    def get_task(self, name):
        if name not in self.ta:
            return None
        return Task(self.ta[name])


class TaskAlternative(object):
    def __init__(self):
        self._alternatives = collections.defaultdict(list)
        self.poisonned = False

    def __repr__(self):
        return '\n'.format(
            '{}: {}'.format(name, ', '.join(str(alt) for alt in alts))
            for name, alts in self._alternatives.items()
        )

    def __iter__(self):
        for name in self._alternatives:
            yield self[name]

    def __contains__(self, name):
        return name in self._alternatives

    def __getitem__(self, name):
        best = heapq.nsmallest(1, self._alternatives[name])
        if not best:
            raise KeyError(name)
        weight, fn = best[0]
        return fn

    def poison(self):
        if self.poisonned:
            return

        debug('Add TaskAlternativeTaskFinder(%r)', self)
        environment.task_finders.append(TaskAlternativeTaskFinder(self))
        self.poisonned = True

    def __call__(self, weight):
        def decorator(fn):
            self.poison()
            heapq.heappush(self._alternatives[fn.__name__], (weight, fn))
            return fn
        return decorator


task_alternative = TaskAlternative()


def optional_import(module_name, package_name=None):
    """
    Tries to import a module and returns either the module or a proxy class
    that raises when accessing an attribute.

    >>> models = optional_import('django.db.models')
    >>> models.Model
        RuntimeError('module django is not installed')
    """
    try:
        module = __import__(module_name)
        if '.' in module_name:
            for segment in module_name.split('.')[1:]:
                module = getattr(module, segment)
        return module
    except ImportError as ie:
        debug('Cannot import %s: %s', module_name, ie)
        return FakeModule(package_name, module_name)


class FakeModule(object):
    def __init__(self, name, module_name):
        self._name = name
        self._module = module_name

    def __getattr__(self, attr):
        if self._module:
            raise RuntimeError('Module {} provided by {} is not installed'.format(
                self._name, self._module))
        raise RuntimeError('Module {} is not installed'.format(self._name))


class BaseInstalledPackages(object):
    def __init__(self):
        self.packages = None

    def __contains__(self, package):
        if self.packages is None:
            self._evaluate()
        debug('package %s is %s', package, 'installed' if package in self.packages else 'uninstalled')
        return package in self.packages

    def _evaluate(self):
        debug('Evaluating packages list')
        self.packages = set(self.evaluate())
        debug('Installed are %s', ', '.join(self.packages))


class Tempdir(object):
    """Context manager for a temporary directory"""

    def __init__(self):
        self.temp_dir = None

    def open(self):
        assert self.temp_dir is None
        self.temp_dir = path(tempfile.mkdtemp())
        return self.temp_dir

    def close(self):
        if self.temp_dir is not None:
            self.temp_dir.rmtree()
            self.temp_dir = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_value, exc_type, tb):
        self.close()


class GitInstall(object):
    """Tool to install a Python package by cloning its git repo and if
    necessary modifying files inside.

    Used as a context manager, it allows to run python code (for instance the
    :class:`LineReplacer` on setup.py or installing patches, etc) after the
    repo has been cloned and before the install. The value returned by entering
    the context manager is the directory in which the repo has been cloned.

    Example: add ``from sett.utils import *`` at the end of the ``__init__.py``

    >>> from paver.easy import *
    >>> with GitInstall('gitlab.enix.org:grocher/sett.git') as sett_dir:
    ...     # Git repository is cloned
    ...     with open(sett_dir.joinpath('sett/__init__.py', 'a+', encoding='utf-8')) as init:
    ...         init.write('\nfrom sett.utils import *\n')
    ... # setup.py install is called
    """
    def __init__(self, repo):
        self.repo = repo
        self._temp_dir = Tempdir()
        self._opened = False

    def open(self):
        """Makes a shallow copy of the repository in a temporary directory"""
        if not self._opened:
            self.temp_dir = self._temp_dir.open()
            call_task('git_copy', args=[self.repo, self.temp_dir])
            self._opened = True
        return self.temp_dir

    def __enter__(self):
        return self.open()

    def install(self):
        """Installs the software by calling setup.py install"""
        with pushd(self.open()):
            sh([sys.executable, self.temp_dir.joinpath('setup.py'), 'install'])

    def close(self):
        """Closes the temporary directory"""
        if not self._opened:
            raise ValueError('Cannot close a unopened instance')
        self._temp_dir.close()
        self._opened = False

    def __exit__(self, exc_value, exc_type, tb):
        try:
            if exc_value is not None:
                self.install()
        finally:
            self.close()

    def __call__(self):
        self.open()
        self.install()
        self.close()

    def patch(self, patch_file, *args, **kw):
        """
        Apply a diff via the patch command on the cloned copy.
        """
        temp_dir = self.open()
        strip = kw.pop('p', 1)
        cmd = [which.patch, '--batch', '-p', str(strip), '-i', patch_file, '-d', temp_dir]
        cmd.extend(args)
        cmd.extend('--{}={}'.format(k, v) for k, v in kw.items())
        sh(cmd)


class LineReplacer(object):
    """
    A tool to replace one or more lines in a file.
    It's an iterator on the line no and the content of the line. The line can
    be changed by assigning it.

    If the pattern is fixed, the :meth:`replace` method will replace all lines
    matching.

    >>> with LineReplacer('setup.py') as setup_py:
    ...     for line_no, line in setup_py:
    ...         if line.startswith('__version__'):
    ...             setup_py[line_no] = line.strip() + '-my-version\n'
    ...     setup_py.replace('import this_lib\n', 'import that_lib as this_lib\n')

    .. warning::

        The lines returned by item, iterator, the arguments to :meth:`replace`
        contains trailing newlines.
    """
    def __init__(self, file, encoding='utf-8'):
        self.file = file
        self.fd = None
        self.lines = None
        self.encoding = encoding

    def open(self):
        self.fd = open(self.file, 'r+', encoding=self.encoding)
        self.lines = self.fd.readlines()
        return self

    def __iter__(self):
        return enumerate(self.lines)

    def close(self):
        try:
            self.fd.seek(0)
            self.fd.truncate()
            self.fd.writelines(self.lines)
        finally:
            self.fd.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_value, exc_type, tb):
        if exc_value is None:
            self.close()
        else:
            self.fd.close()

    def replace(self, value, by):
        for i, line in self:
            if line == value:
                self[i] = by
                break
        else:
            raise ValueError('pattern not found')

    def insert(self, line_no, value):
        self.lines.insert(line_no, value)

    def append(self, value):
        self.lines.append(value)

    def __getitem(self, item):
        return self.lines[item]

    def __setitem__(self, item, value):
        self.lines[item] = value
