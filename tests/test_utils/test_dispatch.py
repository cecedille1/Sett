# -*- coding: utf-8 -*-


import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from sett.utils.dispatch import Dispatcher


class TestDispatcher(unittest.TestCase):
    def test_dispatcher_help(self):
        class MyDispatcher(Dispatcher):
            def help(self):
                'help and stuff'
                pass

        d = MyDispatcher()
        self.assertEqual(d.usage(), 'MyDispatcher [help]\n\t- help: help and stuff')

    def test_call_auto(self):
        m = mock.Mock()

        class MyDispatcher(Dispatcher):
            def auto(self):
                m.auto()

        d = MyDispatcher()
        d()
        m.auto.assert_called_once_with()

    def test_call(self):
        m = mock.Mock()

        class MyDispatcher(Dispatcher):
            def foobar(self):
                m.foobar()

        d = MyDispatcher()
        d('foobar')
        m.foobar.assert_called_once_with()

    def test_call_default(self):
        m = mock.Mock()

        class MyDispatcher(Dispatcher):
            def default(self, name):
                m.default(name)

        d = MyDispatcher()
        d('foobar')
        m.default.assert_called_once_with('foobar')

    def test_call_default_raise(self):
        class MyDispatcher(Dispatcher):
            pass

        d = MyDispatcher()

        with self.assertRaises(NotImplementedError):
            d('foobar')

    def test_on(self):
        m = mock.Mock()

        class MyDispatcher(Dispatcher):
            @Dispatcher.on('foo')
            def bar(self):
                m.bar()

            @Dispatcher.on('foo')
            def baz(self):
                m.baz()

        d = MyDispatcher()

        self.assertEqual(d.foo.__doc__, 'bar, then baz')

        d.foo()
        m.assert_has_calls([
            mock.call.bar(),
            mock.call.baz(),
        ])

    def test_on_super(self):
        m = mock.Mock()

        class MyDispatcher(Dispatcher):
            @Dispatcher.on('foo', -1)
            def before(self):
                m.before()

            @Dispatcher.on('foo')
            def after(self):
                m.after()

            def foo(self):
                'fighter'
                m.foo()

        d = MyDispatcher()

        self.assertEqual(d.foo.__doc__, 'fighter')

        d.foo()
        m.assert_has_calls([
            mock.call.before(),
            mock.call.foo(),
            mock.call.after(),
        ])
