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


from sett import DeployContext, defaults


defaults.UWSGI_SOCKET_TYPE = 'http'


@DeployContext.register
def set_wsgi_application():
    return {
        'wsgi_application': 'sett.pavement'
    }
