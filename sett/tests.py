#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import optparse
import itertools
import importlib

from paver.easy import task, needs, cmdopts, call_task, path, sh, debug, environment
from paver.deps.six import string_types
from sett import which, defaults, task_alternative
from sett.utils.loading import import_string


class NameGenerator(object):
    """
    A collection of utilities to generate names. It takes the prefixes to use
    with module, classes and methods.
    """
    def __init__(self, prefix='test_', cls_prefix='Test', meth_prefix='test_'):
        self._module_prefix = prefix
        self._cls_prefix = cls_prefix
        self._meth_prefix = meth_prefix

    def split(self, value):
        """
        Splits and returns a 3 tuple: root, packages as a list, and the class
        spec. The class spec is a 2 tuple of the class and the method and both
        can be None.
        """
        components = value.split('.')
        root = components.pop(0)
        for i, component in enumerate(components):
            if not component.islower():
                return root, components[:i], (components[i],
                                              components[i + 1] if len(components) > i + 1 else None)
        return root, components, None

    def join(self, *components):
        """
        Joins by a .
        """
        return '.'.join(components)

    def class_join(self, package, cls, method=None):
        """
        Joins by a :
        """
        if method is not None:
            cls = '.'.join([cls, method])
        return ':'.join([package, cls])

    def prefix(self, components):
        """
        Appends the module prefix to a list of modules
        """
        if isinstance(components, string_types):
            return self._prefix(components)
        return (self._prefix(t) for t in components)

    def cls_prefix(self, cls):
        """
        Appends the prefix to  class name
        """
        return '{}{}'.format(self._cls_prefix, cls)

    def method_prefix(self, meth):
        """
        Appends the prefix to meth unless it's None
        """
        return meth and '{}{}'.format(self._meth_prefix, meth)

    def _prefix(self, t):
        return '{}{}'.format(self._module_prefix, t)


def django_package_name_generator(value):
    """
    Uses django strategy, tests is a package.

    auth -> auth.tests
    auth.models -> auth.tests.test_models
    auth.models.User -> auth.tests.test_models:TestUser
    auth.models.User.is_authenticated -> auth.tests.test_models:TestUser.test_is_authenticated
    """
    ng = NameGenerator()
    root, packages, cls = ng.split(value)

    if cls is None:
        return ng.join(root, 'tests', *(ng.prefix(packages)))

    return ng.class_join(
        ng.join(root, 'tests', *(ng.prefix(packages))),
        ng.cls_prefix(cls[0]),
        ng.method_prefix(cls[1]),
    )


def django_module_name_generator(value):
    """
    Uses django strategy, tests is a package.

    auth -> auth.tests
    auth.models -> auth.tests
    auth.models.User -> auth.tests:TestUser
    auth.models.User.is_authenticated -> auth.tests:TestUser.test_is_authenticated
    """
    ng = NameGenerator()
    root, packages, cls = ng.split(value)

    if cls is None:
        return ng.join(root, 'tests')

    return ng.class_join(
        ng.join(root, 'tests'),
        ng.cls_prefix(cls[0]),
        ng.method_prefix(cls[1]),
    )


def ignore_root_name_generator(value):
    """
    A simple strategy for packages with only one module

    auth -> tests
    auth.models -> tests.test_models
    auth.models.User -> tests.test_models:TestUser
    auth.models.User.is_authenticated -> tests.test_models:TestUser.test_is_authenticated
    """
    ng = NameGenerator()
    root, packages, cls = ng.split(value)

    if cls is None:
        return ng.join(defaults.TESTS_ROOT, *(ng.prefix(packages)))

    return ng.class_join(
        ng.join('tests', *(ng.prefix(packages))),
        ng.cls_prefix(cls[0]),
        ng.method_prefix(cls[1]),
    )


def standard_name_generator(value):
    """
    A strategy for any package

    auth -> tests.test_auth
    auth.models -> tests.test_auth.test_models
    auth.models.User -> tests.test_auth.test_models:TestUser
    auth.models.User.is_authenticated -> tests.test_auth.test_models:TestUser.test_is_authenticated
    """
    ng = NameGenerator()
    root, packages, cls = ng.split(value)

    if cls is None:
        return ng.join(defaults.TESTS_ROOT, ng.prefix(root), *(ng.prefix(packages)))

    return ng.class_join(
        ng.join('tests', ng.prefix(root), *(ng.prefix(packages))),
        ng.cls_prefix(cls[0]),
        ng.method_prefix(cls[1]),
    )


def guess_test_name_generator():
    if defaults.TESTS_NAMING_STRATEGY:
        if callable(defaults.TESTS_NAMING_STRATEGY):
            return defaults.TESTS_NAMING_STRATEGY
        return import_string(defaults.TESTS_NAMING_STRATEGY)

    if 'django' in sys.modules:
        return django_module_name_generator

    if len(set(c.split('.', 1)[0] for c in environment.options.setup.get('packages'))) == 1:
        return ignore_root_name_generator
    return standard_name_generator


class NosetestsOptions(object):
    def __init__(self, options=None, test_name_generator=None):
        self._options = options or {}
        self.test_name_generator = test_name_generator or guess_test_name_generator()

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
        return [self.test_name_generator(name) for name in names]

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
            return ['.'.join(itertools.takewhile(str.islower, value.split('.')))
                    for value in values.auto]
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
