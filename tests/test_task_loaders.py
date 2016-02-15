# -*- coding: utf-8 -*-

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from paver.tasks import Environment

from sett.task_loaders import (
    TaskAlternative,
    RegexpTaskLoader,
)


class TestRegexpTaskLoader(unittest.TestCase):
    def test_match(self):
        factory = mock.Mock()
        rtl = RegexpTaskLoader('(\w+):(\d+)', factory)

        self.assertIs(rtl.get_task('abc:123'), factory.return_value)
        factory.assert_called_once_with('abc', '123', task_name='abc:123')

    def test_not_match(self):
        factory = mock.Mock()
        rtl = RegexpTaskLoader('(\w+):(\d+)', factory)
        assert rtl.get_task('abc_123') is None


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
