#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import optparse
import importlib

from paver.easy import task, needs, cmdopts, call_task, path, sh, debug, environment
from sett import which, defaults, task_alternative


class TestsNameGenerator(object):
    def __init__(self, root, strategy, prefix):
        self.prefix = prefix
        if root:
            self.root = [root]
        else:
            self.root = []

        if strategy == 'ignore-first':
            self.start = 1
        else:
            self.start = 0

    def __call__(self, package_name):
        return '.'.join(self.root + [
            self.prefix.format(test)
            for test in package_name.split('.')[self.start:]
        ])


class NosetestsOptions(object):
    def __init__(self, options=None):
        self._options = options or {}

    def __call__(self, values):
        options = {}
        if 'xunit' in values:
            options.update(self.xunit(values.xunit))
        options['tests'] = self.tests(values)
        options.update(self._options)
        return options

    def xunit(self, filename):
        return {
            'with-xunit': True,
            'xunit-file': filename,
            'verbosity': '0',
        }

    def tests(self, options):
        if 'auto' in options:
            return self.auto(options.auto)
        if 'test' in options:
            return options.test

        return self.default_tests()

    def auto(self, names):
        generator = TestsNameGenerator(defaults.TESTS_ROOT,
                                       defaults.TESTS_NAMING,
                                       defaults.TESTS_FILE_PREFIX)
        return [generator(name) for name in names]

    def default_tests(self):
        if defaults.TESTS_ROOT:
            try:
                importlib.import_module(defaults.TESTS_ROOT)
            except ImportError:
                raise RuntimeError('Cannot import the tests, does a package named {} exists?'.format(
                    defaults.TESTS_ROOT,
                ))
            return [defaults.TESTS_ROOT]
        return []


class NosetestsCoverageOptions(NosetestsOptions):
    def __init__(self, options=None):
        options = options or {}
        options.setdefault('cover-erase', True)
        super(NosetestsCoverageOptions, self).__init__(options)

    def __call__(self, values):
        options = super(NosetestsCoverageOptions, self).__call__(values)

        if 'xcoverage' in values:
            options['with-xcoverage'] = True
            options.update(self.xcoverage(values.xcoverage))
        else:
            options['with-coverage'] = True

        options['cover-package'] = self.cover_packages(values)
        return options

    def cover_packages(self, values):
        if 'auto' in values:
            return values.auto
        if 'packages' in values:
            return values.packages
        return list(set(x.split('.')[0]
                        for x in environment.options.setup.get('packages', [])))

    def xcoverage(self, filename):
        return {
            'xcoverage-file': filename,
            'xcoverage-to-stdout': sys.version_info > (3, 0),
        }


@task
@needs(['setup_options'])
@cmdopts([
    optparse.make_option('-t', '--test',
                         action='append',
                         help='Select the test to run'),
    optparse.make_option('-a', '--auto',
                         action='append',
                         metavar='PACKAGE',
                         help='Automatically select the test from a package'),
    optparse.make_option('-x', '--xunit',
                         metavar='COVERAGE_XML_FILE',
                         help='Export a xunit file'),
])
def test(options):
    """Runs the tests"""
    nto = NosetestsOptions()
    return call_task('test_runner', options=nto(options.test))


@task
@needs(['setup_options'])
@cmdopts([
    optparse.make_option('-c', '--packages',
                         action='append',
                         help='Select the packages to cover'),
    optparse.make_option('-t', '--test',
                         action='append',
                         help='Select the test to run'),
    optparse.make_option('-a', '--auto',
                         action='append',
                         metavar='PACKAGE',
                         help='Automatically select the test and the package to cover'),
    optparse.make_option('-x', '--xunit',
                         metavar='XUNIT_FILE',
                         help='Export a xunit file'),
    optparse.make_option('-g', '--xcoverage',
                         metavar='COVERAGE_XML_FILE',
                         help='Export a cobertura file'),
])
def coverage(options):
    """Runs the unit tests and compute the coverage"""
    nto = NosetestsCoverageOptions()
    return call_task('test_runner', options=nto(options.coverage))


@task_alternative(100)
def test_runner(options):
    debug('options are %s', options.test_runner)
    call_task('nosetests', options=options.test_runner)


@task
@needs(['wheel'])
@cmdopts([
    optparse.make_option('-r', '--run',
                         default='',
                         help='Run a command after starting the virutal env'),
    optparse.make_option('-i', '--pypi',
                         default=defaults.PYPI_PACKAGE_INDEX,
                         help='Custom Python Pacakge Index'),
    optparse.make_option('-n', '--name',
                         dest='virtualenv_name',
                         default='test-venv',
                         help='Selects the name of the virtualenv'),
])
def test_archive(options, env):
    if not options.name:
        raise RuntimeError()

    destdir = path(options.test_archive.virtualenv_name)

    if destdir.isdir():
        destdir.rmtree()

    sh([which.virtualenv, '--python', sys.executable, destdir])

    command = [destdir.joinpath('bin/pip'), 'install', env.wheel_file]
    if options.pypi:
        command.extend(['-i', options.pypi])

    sh(command)

    if options.run:
        env_copy = dict(os.environ)
        env_copy['PATH'] += ':{0}'.format(destdir.joinpath('bin'))
        sh(options.run, env=env_copy)
