# -*- coding: utf-8 -*-

import tempfile
import unittest

from sett.source import packagize, FileReplacer
from paver.path import path
from paver.tasks import environment


def test_packagize():
    tmpdir = path(tempfile.mkdtemp())
    try:
        with open(tmpdir.joinpath('x.py'), 'w') as source:
            source.write('AA')

        environment.args = [str(tmpdir.joinpath('x.py'))]
        packagize()
        with open(tmpdir.joinpath('x', '__init__.py'), 'r') as target:
            assert target.read() == 'AA', 'file was not moved'
    except OSError as e:
        assert False, 'file was not created: %s' % e
    finally:
        tmpdir.rmtree()


class TestFileReplace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = path(tempfile.mkdtemp())
        cls.source = cls.tmpdir.joinpath('source')
        cls.target = cls.tmpdir.joinpath('target')

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.rmtree()

    def tearDown(self):
        self.source.remove()
        self.target.remove()

    def setUp(self):
        self.source.touch()
        self.source_inode = self.source.stat().st_ino

    def test_file_replace_exist(self):
        self.target.touch()
        target_inode = self.target.stat().st_ino

        fr = FileReplacer(str(self.source), str(self.target))

        with fr:
            assert self.target.stat().st_ino == self.source_inode

        assert self.source.stat().st_ino == self.source_inode
        assert self.target.stat().st_ino == target_inode

    def test_file_replace_not_exist(self):
        fr = FileReplacer(str(self.source), str(self.target))

        with fr:
            assert self.target.stat().st_ino == self.source_inode

        assert self.source.stat().st_ino == self.source_inode
        assert not self.target.exists()

    def test_decorates(self):
        fr = FileReplacer(str(self.source), str(self.target))
        return_value = object()

        @fr
        def test():
            assert self.target.stat().st_ino == self.source_inode
            return return_value

        assert test() is return_value
