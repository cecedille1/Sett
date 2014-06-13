#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os

from StringIO import StringIO
from tarfile import TarFile

from paver.easy import task, call_task, path, no_help, consume_nargs, needs
from paver.setuputils import setup


try:
    from setup import build_info
except ImportError:
    sys.path.append('.')
    from setup import build_info


try:
    import requests
except ImportError as e:
    requests = None


@task
@consume_nargs(2)
def install_remote_tar(args):
    """Extracts an archive in a directory"""
    web_archive, destination = args

    if '://' in web_archive:
        if requests is None:
            raise ValueError('Missing required lib requests')
        sys.stderr.write('Downloading from {0}\n'.format(web_archive))
        dl = requests.get(web_archive)

        tf = TarFile.open(path(web_archive).basename(),
                          'r:*', fileobj=StringIO(dl.content))
    else:
        tf = TarFile.open(web_archive)

    path(destination).rmtree()

    for ti in tf.getmembers():
        name = path(ti.name)
        if name.basename() == 'index.html':
            web_root = name.dirname()
            break
    else:
        raise ValueError('Missing index.html')

    tf.extractall('temp/')
    tf.close()

    path(os.path.join('temp', web_root)).move(destination)
    path('temp').rmdir()


@task
@no_help
def setup_options(options):
    setup(**build_info)


@task
def clean():
    """Clean the workspace"""
    path('dist').rmtree()


@task
@needs(['setup_options'])
def make(options):
    """Overrides sdist to make sure that our setup.py is generated."""
    call_task('sdist')

    is_prerelease = (
        'a' in options.setup.version or
        'b' in options.setup.version or
        'rc' in options.setup.version
    )
    if not is_prerelease:
        target = '{name}-{version}.tar.gz'.format(**options.setup)
        link = 'dist/{name}-latest.tar.gz'.format(**options.setup)
        path(link).unlink_p()

        sys.stderr.write('Link {0} to {1}\n'.format(link, target))
        path(target).symlink(link)
