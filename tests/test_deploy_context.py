# -*- coding: utf-8 -*-

from sett.deploy_context import DeployContextFactory


def test_precedence():
    """
    Test precedence rules:

        call    regd     reg    expected
    ------------------------------------
    a    1       2        3        3
    b            1        2        2
    c    1       2                 2
    d    1                2        2
    e    1                         1
    """
    DeployContext = DeployContextFactory()

    DeployContext.register(a=3, b=2, d=2)
    DeployContext.register_default(a=2, b=1, c=2)

    actual = DeployContext({'a': 1, 'c': 1, 'd': 1, 'e': 1})
    assert actual == {'a': 3, 'b': 2, 'c': 2, 'd': 2, 'e': 1}, actual


def test_list():
    DeployContext = DeployContextFactory()
    DeployContext.register(a=['abc'])
    DeployContext.register(a=['def'])

    actual = DeployContext()
    assert actual == {'a': ['abc', 'def']}, actual


def test_dict():
    DeployContext = DeployContextFactory()
    DeployContext.register(a={'a': 'abc'})
    DeployContext.register(a={'b': 'def'})

    actual = DeployContext()
    assert actual == {'a': {'a': 'abc', 'b': 'def'}}, actual
