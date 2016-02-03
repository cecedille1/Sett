#!/usr/bin/env python
# -*- coding: utf-8 -*-


DISABLED_LIBS = ['django']

try:
    import sett  # noqa
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))


from paver.easy import task, call_task
from paver.deps.six import exec_

from sett import ROOT
from sett.source import FileReplacer


def find_version(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'rt') as init:
        for line in init:
            if line.startswith('__version__'):
                x, version = line.split('=', 1)
                return version.strip().strip('\'"')
        else:
            raise ValueError('Cannot find the version in {0}'.format(filename))


def parse_requirements(requirements_txt):
    requirements = []
    try:
        with open(requirements_txt, 'rt') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                if line.startswith('-'):
                    raise ValueError('Unexpected command {0} in {1}'.format(
                        line,
                        requirements_txt,
                    ))

                requirements.append(line)
        return requirements
    except IOError:
        return []


@task
def setup_options():
    from paver.setuputils import setup
    import setuptools

    setup(
        name='sett',
        version=find_version('sett/__init__.py'),
        packages=setuptools.find_packages(
            include=[
                'sett',
            ],
            exclude=[
            ]
        ),
        url='https://github.org/cecedille1/sett',
        author=u'Grégoire ROCHER',
        author_email='gr@enix.org',
        install_requires=parse_requirements('requirements.txt'),
        include_package_data=True,
    )


@task
@FileReplacer(ROOT.joinpath('requirements_minimal.txt'), ROOT.joinpath('requirements.txt'))
def make_minimal():
    call_task('sett.build.make')


try:
    with open(ROOT.joinpath('localpavement.py'), 'r') as localpavement:
        exec_(localpavement.read(), locals(), globals())
except (IOError, ImportError) as e:
    pass
