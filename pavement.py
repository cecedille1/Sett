#!/usr/bin/env python
# -*- coding: utf-8 -*-


DISABLED_LIBS = ['django']

try:
    import sett
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    import sett


from paver.easy import task, call_task
from sett import DeployContext, defaults, ROOT
from sett.source import FileReplacer


defaults.UWSGI_SOCKET_TYPE = 'http'


@DeployContext.register
def set_wsgi_application():
    return {
        'wsgi_application': 'sett.pavement'
    }


@task
@FileReplacer(ROOT.joinpath('requirements_minimal.txt'), ROOT.joinpath('requirements.txt'))
def make_minimal():
    call_task('sett.build.make')
