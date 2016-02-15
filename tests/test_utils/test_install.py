# -*- coding: utf-8 -*-

import sys
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from paver.path import path
from sett.utils.fs import Tempdir
from sett.utils.install import GitInstall, Git


class TestGitInstall(unittest.TestCase):
    def setUp(self):
        self.git = mock.Mock(spec=Git)
        with mock.patch('sett.utils.install.Tempdir', spec=Tempdir) as tdir:
            self.gi = GitInstall('git-repository-url', self.git)
        self.tdir = tdir.return_value
        self.path = self.tdir.open.return_value = path('/abc')

    def test_open(self):
        self.gi.open()
        assert self.tdir.open.called_once
        self.git.clone.assert_called_once_with('git-repository-url', self.path)

    def test_open_twice(self):
        r1 = self.gi.open()
        r2 = self.gi.open()

        assert r1 == r2
        assert self.tdir.open.called_once

    def test_close_unopened(self):
        self.assertRaises(ValueError, self.gi.close)

    def test_close(self):
        self.gi.open()
        self.gi.close()
        assert self.tdir.close.called_once()

    def test_install(self):
        self.gi.open()
        sh, pushd = mock.Mock(), mock.MagicMock()
        with mock.patch.multiple('sett.utils.install', sh=sh, pushd=pushd):
            self.gi.install()

        pushd.assert_called_once_with('/abc')
        sh.assert_called_once_with([sys.executable, '/abc/setup.py', 'install'])

    def test_open_install(self):
        sh, pushd = mock.Mock(), mock.MagicMock()
        with mock.patch.multiple('sett.utils.install', sh=sh, pushd=pushd):
            self.gi.install()

        pushd.assert_called_once_with('/abc')
        sh.assert_called_once_with([sys.executable, '/abc/setup.py', 'install'])

    def test_patch_args(self):
        self.gi.open()

        sh, which = mock.Mock(), mock.Mock()
        with mock.patch.multiple('sett.utils.install', sh=sh, which=which):
            self.gi.patch('def.patch', '-a', '-b', '-c', ghi='klm')

        sh.assert_called_once_with([
            which.patch,
            '--batch', '-p', '1',
            '-i', 'def.patch',
            '-d', '/abc',
            '-a', '-b', '-c',
            '--ghi=klm',
        ])

    def test_patch(self):
        self.gi.open()

        sh, which = mock.Mock(), mock.Mock()
        with mock.patch.multiple('sett.utils.install', sh=sh, which=which):
            self.gi.patch('def.patch')

        sh.assert_called_once_with([
            which.patch,
            '--batch', '-p', '1',
            '-i', 'def.patch',
            '-d', '/abc',
        ])

    def test_context_manager(self):
        with mock.patch.object(self.gi, 'open') as o,\
                mock.patch.object(self.gi, 'close') as c,\
                mock.patch.object(self.gi, 'install') as i:
            with self.gi as value:
                assert value is o.return_value
        o.assert_called_once_with()
        i.assert_called_once_with()
        c.assert_called_once_with()

    def test_context_manager_exc(self):
        with mock.patch.object(self.gi, 'open') as o,\
                mock.patch.object(self.gi, 'close') as c,\
                mock.patch.object(self.gi, 'install') as i:
            try:
                with self.gi:
                    raise ValueError
            except ValueError:
                pass

        o.assert_called_once_with()
        i.assert_not_called()
        c.assert_called_once_with()
