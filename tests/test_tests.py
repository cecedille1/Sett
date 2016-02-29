# -*- coding: utf-8 -*-


import unittest

from sett.tests import (
    django_package_name_generator,
    django_module_name_generator,
    ignore_root_name_generator,
    standard_name_generator,
)


class Test_django_package_name_generator(unittest.TestCase):
    def test_module(self):
        self.assertEqual(django_package_name_generator('auth'),
                         'auth.tests')

    def test_package(self):
        self.assertEqual(django_package_name_generator('auth.models'),
                         'auth.tests.test_models')

    def test_class(self):
        self.assertEqual(django_package_name_generator('auth.models.User'),
                         'auth.tests.test_models:TestUser')

    def test_method(self):
        self.assertEqual(django_package_name_generator('auth.models.User.is_authenticated'),
                         'auth.tests.test_models:TestUser.test_is_authenticated')


class Test_django_module_name_generator(unittest.TestCase):
    def test_module(self):
        self.assertEqual(django_module_name_generator('auth'),
                         'auth.tests')

    def test_package(self):
        self.assertEqual(django_module_name_generator('auth.models'),
                         'auth.tests')

    def test_class(self):
        self.assertEqual(django_module_name_generator('auth.models.User'),
                         'auth.tests:TestUser')

    def test_method(self):
        self.assertEqual(django_module_name_generator('auth.models.User.is_authenticated'),
                         'auth.tests:TestUser.test_is_authenticated')


class Test_ignore_root_name_generator(unittest.TestCase):
    def test_module(self):
        self.assertEqual(ignore_root_name_generator('auth'),
                         'tests')

    def test_package(self):
        self.assertEqual(ignore_root_name_generator('auth.models'),
                         'tests.test_models')

    def test_class(self):
        self.assertEqual(ignore_root_name_generator('auth.models.User'),
                         'tests.test_models:TestUser')

    def test_method(self):
        self.assertEqual(ignore_root_name_generator('auth.models.User.is_authenticated'),
                         'tests.test_models:TestUser.test_is_authenticated')


class Test_standard_name_generator(unittest.TestCase):
    def test_module(self):
        self.assertEqual(standard_name_generator('auth'),
                         'tests.test_auth')

    def test_package(self):
        self.assertEqual(standard_name_generator('auth.models'),
                         'tests.test_auth.test_models')

    def test_class(self):
        self.assertEqual(standard_name_generator('auth.models.User'),
                         'tests.test_auth.test_models:TestUser')

    def test_method(self):
        self.assertEqual(standard_name_generator('auth.models.User.is_authenticated'),
                         'tests.test_auth.test_models:TestUser.test_is_authenticated')
