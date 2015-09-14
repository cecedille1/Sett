#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import optparse
import tempfile
import io

from tarfile import TarFile

from paver.easy import task, path, consume_nargs, info, cmdopts

from sett import defaults
from sett.utils import optional_import

requests = optional_import('requests')


class TarExtract(object):
    def __init__(self, web_archive):
        self.web_archive = web_archive
        self.tf = None

    def __enter__(self):
        if self.tf is not None:
            raise ValueError('Cannot re-enter')

        if '://' in self.web_archive:
            info('Downloading from {0}'.format(self.web_archive))
            dl = requests.get(self.web_archive)

            self.tf = TarFile.open(path(self.web_archive).basename(),
                                   'r:*', fileobj=io.BytesIO(dl.content))
        else:
            self.tf = TarFile.open(self.web_archive)
        return self.tf

    def __exit__(self, exc_value, exc_type, traceback):
        self.tf.close()


@task
@consume_nargs(2)
@cmdopts([
    optparse.make_option(
        '-t', '--target',
        default=defaults.TAR_ROOT_FILE_MARKER,
        help='The target filename'
    )
])
def install_remote_tar(args, options):
    """Usage: install_remote_tar [-t|--target TARGET] ARCHIVE DESTINATION

Extracts an archive in a directory. The archive is either a file on the local
file system or a remote URL fetched by http/https. A file whose name is TARGET
is looked for inside the archive and the directory containing the target is
moved as the DESTINATION directory.

Any exisiting directory will be removed before the new directory is copied.
"""
    web_archive, destination = args

    target = getattr(options, 'target', 'index.html')

    temp_dir = path(tempfile.mkdtemp())
    try:
        with TarExtract(web_archive) as tf:
            for ti in sorted(tf.getmembers(), key=lambda x: (x.name.count('/'), x.name)):
                name = path(ti.name)
                if name.basename() == target:
                    target_root = name.dirname()
                    break
            else:
                raise ValueError('Missing target: {}'.format(target))
            tf.extractall(temp_dir)
    except Exception:
        temp_dir.rmtree()
        raise
    else:
        path(destination).rmtree()
        temp_dir.joinpath(target_root).move(destination)


@task
@consume_nargs(3)
def extract_from_tar(args):
    """Usage: extract_from_tar archive target_file destination
    Extract from the *archive* the file *target_file* and puts it into *destination*
    """
    web_archive, filename, destination = args

    path(destination).dirname().makedirs()

    if destination.endswith('/'):
        destination = os.path.join(destination, filename)

    with TarExtract(web_archive) as tf:
        for ti in tf.getmembers():
            if path(ti.name).basename() == filename:
                break
        else:
            raise ValueError('No file "{0}" in the archive'.format(filename))

        file = tf.extractfile(ti)
        info('Writing to {0}'.format(destination))
        with open(destination, 'wb') as dest:
            dest.write(file.read())
