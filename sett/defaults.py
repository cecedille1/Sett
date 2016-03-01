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
TESTS_NAMING_STRATEGY = None


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

"""
.. property:: UWSGI_OUTPUT_FORMAT

    The format of the configuration file generated for uwsgi. Can be `None`,
    xml or yml.  None will check if pyyaml is installed and use yml or default
    to xml
"""
UWSGI_OUTPUT_FORMAT = None

UWSGI_EXTRA = {}


SUPERVISORDCONF = 'etc/supervisord/supervisord.conf'

# A list or a ':' joined string of path to include in the generation of Sass files
SASS_PATH = os.environ.get('SASS_PATH', '')
