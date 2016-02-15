# -*- coding: utf-8 -*-


from sett.utils.loading import optional_import


def test_optional_import():
    from sett import utils
    assert optional_import('sett.utils') is utils


def test_optional_import_fail():
    foo_bar = optional_import('foo.bar')
    assert not foo_bar, 'FakeModule should be falsy'

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
