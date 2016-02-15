# -*- coding: utf-8 -*-


import subprocess
from paver.path import path
from sett import which, ROOT

pavements = path(__file__).dirname().joinpath('pavements')


def eval_paver(pavement, *args):
    pavement = pavements.joinpath(pavement)
    command = [which.paver, '-q', '-f', pavement]
    command.extend(args)

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            'LC_ALL': 'C',
            'PYTHONPATH': ROOT,
        }
    )
    out = process.stdout.read()
    assert process.wait() == 0, 'OUT: {}\nERR: {}\n'.format(out, process.stderr.read())
    return out.decode('utf-8')


def test_1_t():
    evaluation = eval_paver('test_1.py', 't')
    assert evaluation == 't1\n', repr(evaluation)


def test_1_t1():
    evaluation = eval_paver('test_1.py', 't1')
    assert evaluation == 't1\n', repr(evaluation)
