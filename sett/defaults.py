#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

USE_THREADING = os.environ.get('LINEAR', 'no').lower() != 'yes'

HTTP_WSGI_IP = 'localhost'
HTTP_WSGI_PORT = 8000
STATIC_SERVER = 'nginx'

# The name of the default requirements file
REQUIREMENTS = 'requirements.txt'

# The name of the directory in which ruby gems are installed
GEM_HOME = 'gem'

# The file that indicates the directory in tar
TAR_ROOT_FILE_MARKER = 'index.html'


# The URL used to push the packages (pip upload)
PYPI_REPOSITORY = 'http://enixpi.enix.org/'
PYPI_REPOSITORY_IGNORE_SSL = False

# The URL used to fetch the packages (pip install -i)
PYPI_PACKAGE_INDEX = 'https://enixpi.enix.org/simple/'
PYPI_PACKAGE_INDEX_IGNORE_SSL = False


# The name of the directory containing compass sass sources
SASS_SRC_DIR = COMPASS_DIR = 'compass/'

# The destination of the built CSS files, absolute or relative to ROOT
SASS_BUILD_DIR = 'static/css'

# The style of the CSS ouput
SASS_OUTPUT_STYLE = 'compact'

SASS_FUNCTIONS = []

SCSS_LINT_CONFIG = 'compass/.scss-lint.yml'


DJANGO_SETTINGS_FILE = ['settings.py']


CURL_EXTRA_HEADERS = {}

TESTS_ROOT = 'tests'
TESTS_FILE_PREFIX = 'test_{}'

"""
.. property::TESTS_NAMING

    The strategy to use in order to find the test file from the package name.
    The naming strategy is optional and allow to use the ``-a`` flag of the
    tests command. This flag will run only the tests corresponding to a module,
    class, etc.

Tests strategies
----------------

- **none**: The tests for are module are in a separate directory TESTS_ROOT and
named as the module with the prefix TESTS_FILE_PREFIX.

Example:

Source                      Test
=========================== =================================
django_app.models           tests.test_django_app.test_models
other_app.views             tests.test_other_app.test_views


- **ignore-first** : The tests for a module are in a separate directory
TESTS_ROOT and named as the module with the prefix TESTS_FILE_PREFIX. The root
module is ignored.  This strategy is suitable when a package contains only one
module and no code in the ``__init__.py``.

Example:

Source                      Test
=========================== =============================
django.shortcuts            tests.test_shortcuts
django.views.generic        tests.test_views.test_generic
"""

TESTS_NAMING = 'ignore-first'


RJS_BUILD_DIR = 'build/static/js'
RJS_CONFIG = 'config.js'
RJS_OPTIMIZE = 'uglify2'


DEPLOY_TEMPLATES_DIR = 'sett-templates'
DOMAIN_TEMPLATE = 'dev.{name}.emencia.net'
NGINX_TEMPLATE = 'nginx.conf.jinja'
MONIT_TEMPLATE = 'monit.conf.jinja'
SYSTEMD_TEMPLATE = 'systemd.service.jinja'


"""
.. property:: UWSGI_SOCKET_TYPE

    value unix or http. The type of unix socket to use
"""
UWSGI_SOCKET_TYPE = 'unix'

UWSGI_EXTRA = {}


SUPERVISORDCONF = 'etc/supervisord/supervisord.conf'

# A list or a ':' joined string of path to include in the generation of Sass files
SASS_PATH = os.environ.get('SASS_PATH', '')
