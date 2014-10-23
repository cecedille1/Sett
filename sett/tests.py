#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os.path
import optparse
from paver.easy import task, needs, cmdopts, call_task, path, sh


def _nosetests(options):
    nosetest_options = {}

    if hasattr(options, 'xunit'):
        nosetest_options.update({
            'with-xunit': True,
            'xunit-file': options.xunit,
            'verbosity': '0',
        })

    if hasattr(options, 'auto'):
        tests = [
            ('tests.' + '.'.join('test_{0}'.format(test) for test in auto.split('.')[1:]))
            for auto in options.auto]
    elif hasattr(options, 'test'):
        tests = options.test
    else:
        try:
            import tests
        except ImportError:
            tests = []
        else:
            tests = ['tests']

    nosetest_options['tests'] = tests
    return nosetest_options


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
    return call_task('nosetests', options=_nosetests(options.test))


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

    nosetest_options = _nosetests(options.coverage)
    nosetest_options.update({
        'cover-erase': True,
    })

    if hasattr(options.coverage, 'xcoverage'):
        nosetest_options.update({
            'with-xcoverage': True,
            'xcoverage-file': options.coverage.xcoverage,
            'xcoverage-to-stdout': False,
        })
    else:
        nosetest_options.update({
            'with-coverage': True,
        })

    if hasattr(options.coverage, 'auto'):
        packages = options.coverage.auto
    elif hasattr(options.coverage, 'packages'):
        packages = options.coverage.packages
    else:
        packages = list(set(x.split('.')[0] for x in options.setup.get('packages')))

    nosetest_options.update({
        'cover-package': packages,
    })

    return call_task('nosetests', options=nosetest_options)


@task
@needs(['setup_options'])
@cmdopts([
    optparse.make_option('-r', '--run',
                         default='',
                         help='Run a command after starting the virutal env'),
    optparse.make_option('-i', '--pypi',
                         default='',
                         help='Custom Python Pacakge Index'),
    optparse.make_option('-n', '--name',
                         dest='virtualenv_name',
                         default='test-venv',
                         help='Selects the name of the virtualenv'),
])
def test_archive(options):
    if not options.name:
        raise RuntimeError()

    destdir = path(options.test_archive.virtualenv_name)

    if destdir.isdir():
        destdir.rmtree()

    target = 'dist/{name}-{version}.tar.gz'.format(**options.setup)
    sh(['virtualenv', '--python', 'python2', destdir])

    command = [os.path.join(destdir, 'bin/pip'), 'install', target]
    if options.pypi:
        command.extend(['-i', options.pypi])

    sh(command)

    if options.run:
        env_copy = dict(os.environ)
        env_copy['PATH'] += ':{0}/bin/'.format(destdir)
        sh(options.run, env=env_copy)
