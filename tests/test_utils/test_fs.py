# -*- coding: utf-8 -*-


import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock


from sett.utils.fs import Tempdir, LineReplacer


def test_Tempdir():
    try:
        with Tempdir() as tdir:
            assert tdir.isdir(), 'Tempdir was not created'
            exc = Exception()
            raise exc
    except Exception as e:
        assert e is exc
        assert not tdir.exists(), 'Tempdir was not deleted'


class TestLineReplacer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_open = mock.patch('sett.utils.fs.open', create=True)

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
