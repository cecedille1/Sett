# -*- coding: utf-8 -*-

import sys

from paver.easy import debug, pushd, sh

from sett.utils.fs import Tempdir
from sett.bin import which


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


class Git(object):
    def clone(self, repo, target, depth=1):
        return self('clone', '--depth', str(depth), repo, target)

    def __call__(self, *args):
        cmd = [which.git]
        cmd.extend(args)
        return sh(cmd)


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
    def __init__(self, repo, git=None):
        self.repo = repo
        self._temp_dir = Tempdir()
        self._opened = False
        self._git = git or Git()

    def open(self):
        """Makes a shallow copy of the repository in a temporary directory"""
        if not self._opened:
            self.temp_dir = self._temp_dir.open()
            self._git.clone(self.repo, self.temp_dir)
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
            if exc_value is None:
                self.install()
        finally:
            self.close()

    def __call__(self):
        try:
            self.open()
            self.install()
        finally:
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
