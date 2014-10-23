#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from StringIO import StringIO
from tarfile import TarFile

from paver.easy import task, path, consume_nargs, info


try:
    import requests
except ImportError as e:
    requests = None


class TarExtract(object):
    def __init__(self, web_archive, temp_dir='./temp'):
        self.web_archive = web_archive
        self.tf = None

    def __enter__(self):
        if self.tf is not None:
            raise ValueError('Cannot re-enter')

        if '://' in self.web_archive:
            if requests is None:
                raise ValueError('Missing required lib requests')
            info('Downloading from {0}'.format(self.web_archive))
            dl = requests.get(self.web_archive)

            self.tf = TarFile.open(path(self.web_archive).basename(),
                                   'r:*', fileobj=StringIO(dl.content))
        else:
            self.tf = TarFile.open(self.web_archive)
        return self.tf

    def __exit__(self, exc_value, exc_type, traceback):
        self.tf.close()


@task
@consume_nargs(2)
def install_remote_tar(args):
    """Extracts an archive in a directory"""
    web_archive, destination = args
    temp_dir = './tmp/'

    path(destination).rmtree()
    with TarExtract(web_archive) as tf:
        tf.extractall(temp_dir)

        for ti in tf.getmembers():
            name = path(ti.name)
            if name.basename() == 'index.html':
                web_root = name.dirname()
                break
        else:
            raise ValueError('Missing index.html')

        path(os.path.join(temp_dir, web_root)).move(destination)


@task
@consume_nargs(3)
def extract_from_tar(args):
    web_archive, filename, destination = args
    with TarExtract(web_archive) as tf:
        for ti in tf.getmembers():
            if path(ti.name).basename() == filename:
                break
        else:
            raise ValueError('No file "{0}" in the archive'.format(filename))

        file = tf.extractfile(ti)

        path(destination).dirname().makedirs()

        info('Writing to {0}'.format(destination))
        with open(destination, 'wb') as dest:
            dest.write(file.read())
