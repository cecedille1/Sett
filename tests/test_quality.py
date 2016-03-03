# -*- coding: utf-8 -*-


import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from paver.tasks import Environment, task
from paver.options import Bunch
from sett.quality import quality


environment = Environment(__import__('tests.test_quality'))


@task
def setup_options():
    environment.options = Bunch({'setup': Bunch({'packages': []})})


@mock.patch('paver.tasks.environment', environment)
class Test_quality(unittest.TestCase):
    def test_quality_warning_code(self):
        with mock.patch('sett.quality.sh') as sh:
            sh.return_value = '''
test/test_quality.py:14:9: E121 this and that
test/test_quality.py:14:9: W292 this and that
'''
            try:
                quality()
            except SystemExit:
                raise AssertionError('should not have raised SystemExit')

    def test_quality_error_code(self):
        with mock.patch('sett.quality.sh') as sh:
            sh.return_value = '''
test/test_quality.py:14:9: E121 this and that
test/test_quality.py:14:9: W504 this and that
'''
            try:
                quality()
            except SystemExit:
                pass
            else:
                raise AssertionError('should have raised SystemExit')
