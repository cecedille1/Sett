# -*- coding: utf-8 -*-


import unittest
import os.path

try:
    import unittest.mock
except ImportError:
    import mock

from sett.bin import DirectorySearcher, NotInstalled, Which, LazyWhich


class TestDirectorySearcher(unittest.TestCase):
    def setUp(self):
        self.root = os.path.join(os.path.dirname(__file__), 'bin')
        self.ds = DirectorySearcher(self.root)

    def test_search(self):
        executable = os.path.join(self.root, 'executable')
        self.assertEqual(self.ds.search('executable'), executable)

    def test_search_not_x(self):
        self.assertIsNone(self.ds.search('not-executable'))

    def test_search_not_exits(self):
        self.assertIsNone(self.ds.search('not-found'))


class TestWhich(unittest.TestCase):
    def setUp(self):
        self.p1 = mock.Mock(spec=DirectorySearcher)
        self.p2 = mock.Mock(spec=DirectorySearcher)
        self.p1.search.return_value = self.p2.search.return_value = None
        self.which = Which([self.p1, self.p2])

    def test_search(self):
        executable = self.p1.search.return_value = mock.Mock()
        self.assertEqual(self.which.search('executable'), executable)
        self.p1.search.assert_called_once_with('executable')
        assert self.p2.call_count == 0

    def test_search_cache(self):
        executable = self.p1.search.return_value = mock.Mock()
        self.assertEqual(self.which.search('executable'), executable)
        self.assertEqual(self.which.search('executable'), executable)
        self.p1.search.assert_called_once_with('executable')
        assert self.p2.call_count == 0

    def test_search_precendence(self):
        e1 = self.p1.search.return_value = mock.Mock()
        self.p2.search.return_value = mock.Mock()
        self.assertEqual(self.which.search('executable'), e1)

    def test_attribute(self):
        executable = self.p1.search.return_value = mock.Mock()
        self.assertEqual(self.which.executable, executable)

    def test_search_not_exits(self):
        with self.assertRaises(NotInstalled):
            self.which.search('not-found')


def test_lazy_which_attribute():
    p = mock.Mock()
    m = mock.Mock(return_value=[p])
    lw = LazyWhich(m)
    assert lw.search('a') == p.search.return_value

    assert lw.search('b') == p.search.return_value
    assert p.search.has_calls([
        mock.call.search('a'),
        mock.call.search('b'),
    ])


def test_lazy_which():
    m = mock.Mock(return_value=[mock.Mock()])
    lw = LazyWhich(m)
    assert m.call_count == 0

    lw.search('a')
    assert m.call_count == 1

    lw.search('b')
    assert m.call_count == 1


def test_lazy_which_evaluate():
    m = mock.Mock(return_value=[mock.Mock()])
    lw = LazyWhich(m)

    @lw.update
    def action():
        pass

    lw.search('a')
    action()

    lw.search('a')
    assert m.call_count == 2, '%s != %s' % (m.call_count, 2)
