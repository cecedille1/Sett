# -*- coding: utf-8 -*-


try:
    from unittest import mock
except ImportError:
    import mock

from paver.easy import environment, Bunch
from sett.quality import quality


def test_quality_warning_code():
    environment.options = Bunch({'setup': Bunch({'packages': []})})
    with mock.patch('sett.quality.sh') as sh:
        sh.return_value = '''
test/test_quality.py:14:9: E121 this and that
test/test_quality.py:14:9: W292 this and that
'''
        try:
            quality()
        except SystemExit:
            raise AssertionError('should not have raised SystemExit')


def test_quality_error_code():
    environment.options = Bunch({'setup': Bunch({'packages': []})})
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
