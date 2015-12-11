# -*- coding: utf-8 -*-

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

import sys

from paver.path import path
from paver.tasks import Environment
from sett.utils import (
    task_name,
    TaskAlternative,
    TaskAlternativeTaskFinder,
    optional_import,
    Tempdir,
    GitInstall,
    LineReplacer,
)


def test_task_name():
    def fn():
        pass

    decorated = task_name('my_name')(fn)
    assert decorated.__name__ == 'my_name'


class TestTaskAlternative(unittest.TestCase):
    def setUp(self):
        self.env = Environment()
        self.ta = TaskAlternative(self.env)

    def test_get_alternative_first(self):
        @self.ta(1)
        def a():
            pass

        @self.ta(2, name='a')
        def b():
            pass

        assert self.ta['a'] is a

    def test_get_alternative_second(self):
        @self.ta(2)
        def a():
            pass

        @self.ta(1, name='a')
        def b():
            pass

        assert self.ta['a'] is b


def test_optional_import():
    from sett import utils
    assert optional_import('sett.utils') is utils


def test_optional_import_fail():
    foo_bar = optional_import('foo.bar')
    try:
        foo_bar.baz
    except AttributeError:
        assert False, '{} is  not a FakeModule'.format(foo_bar)
    except RuntimeError as rte:
        assert str(rte) == 'Module foo.bar is not installed', str(rte)


def test_optional_import_fail_name():
    foo_bar = optional_import('foo.bar', 'foobar-python')
    try:
        foo_bar.baz
    except AttributeError:
        assert False, '{} is  not a FakeModule'.format(foo_bar)
    except RuntimeError as rte:
        assert str(rte) == 'Module foo.bar provided by foobar-python is not installed', str(rte)


def test_Tempdir():
    try:
        with Tempdir() as tdir:
            assert tdir.isdir(), 'Tempdir was not created'
            exc = Exception()
            raise exc
    except Exception as e:
        assert e is exc
        assert not tdir.exists(), 'Tempdir was not deleted'


class TestGitInstall(unittest.TestCase):
    def setUp(self):
        with mock.patch('sett.utils.Tempdir', spec=Tempdir) as tdir:
            self.gi = GitInstall('git-repository-url')
        self.tdir = tdir.return_value
        self.path = self.tdir.open.return_value = path('/abc')

    def test_open(self):
        with mock.patch('sett.utils.call_task') as call_task:
            self.gi.open()

        assert self.tdir.open.called_once
        assert not call_task.assert_called_once_with('git_copy', args=[
            'git-repository-url', self.path,
        ])

    def test_open_twice(self):
        with mock.patch('sett.utils.call_task'):
            r1 = self.gi.open()
        r2 = self.gi.open()

        assert r1 == r2
        assert self.tdir.open.called_once

    def test_close_unopened(self):
        self.assertRaises(ValueError, self.gi.close)

    def test_close(self):
        with mock.patch('sett.utils.call_task'):
            self.gi.open()

        self.gi.close()
        assert self.tdir.close.called_once()

    def test_install(self):
        with mock.patch('sett.utils.call_task'):
            self.gi.open()

        sh, pushd = mock.Mock(), mock.MagicMock()
        with mock.patch.multiple('sett.utils', sh=sh, pushd=pushd):
            self.gi.install()

        pushd.assert_called_once_with('/abc')
        sh.assert_called_once_with([sys.executable, '/abc/setup.py', 'install'])

    def test_open_install(self):
        with mock.patch('sett.utils.call_task'), mock.patch('sett.utils.sh') as sh, mock.patch('sett.utils.pushd') as pushd:
            self.gi.install()

        pushd.assert_called_once_with('/abc')
        sh.assert_called_once_with([sys.executable, '/abc/setup.py', 'install'])

    def test_patch_args(self):
        with mock.patch('sett.utils.call_task'):
            self.gi.open()

        sh, which = mock.Mock(), mock.Mock()
        with mock.patch.multiple('sett.utils', sh=sh, which=which):
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
        with mock.patch('sett.utils.call_task'):
            self.gi.open()

        sh, which = mock.Mock(), mock.Mock()
        with mock.patch.multiple('sett.utils', sh=sh, which=which):
            self.gi.patch('def.patch')

        sh.assert_called_once_with([
            which.patch,
            '--batch', '-p', '1',
            '-i', 'def.patch',
            '-d', '/abc',
        ])

    def test_context_manager(self):
        with mock.patch('sett.utils.call_task'),\
                mock.patch.object(self.gi, 'open') as o,\
                mock.patch.object(self.gi, 'close') as c,\
                mock.patch.object(self.gi, 'install') as i:
            with self.gi as value:
                assert value is o.return_value
        o.assert_called_once_with()
        i.assert_called_once_with()
        c.assert_called_once_with()

    def test_context_manager_exc(self):
        with mock.patch('sett.utils.call_task'),\
                mock.patch.object(self.gi, 'open') as o,\
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


class TestLineReplacer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_open = mock.patch('sett.utils.open', create=True)

    def setUp(self):
        self.lr = LineReplacer('abc.txt')
        self.Opn = self.patch_open.start()
        self.opn = self.Opn.return_value
        self.opn.readlines.return_value = ['abc', 'def', 'ghi']

    def tearDown(self):
        self.patch_open.stop()

    def test_open(self):
        self.lr.open()
        self.Opn.assert_called_once_with('abc.txt', 'r+', encoding='utf-8')

    def test_iterator(self):
        self.lr.open()
        lst = list(self.lr)
        self.assertEqual(lst, [(0, 'abc'), (1, 'def'), (2, 'ghi')])

    def test_close(self):
        self.lr.open()
        self.lr.close()
        self.opn.assert_has_calls([
            mock.call.seek(0),
            mock.call.truncate(),
            mock.call.writelines(['abc', 'def', 'ghi']),
            mock.call.close(),
        ])

    def test_replace(self):
        with self.lr:
            self.lr.replace('def', 'fed')
        self.opn.writelines.assert_called_once_with(['abc', 'fed', 'ghi'])
