# -*- coding: utf-8 -*-


from sett.utils.task import task_name


def test_task_name():
    def fn():
        pass

    decorated = task_name('my_name')(fn)
    assert decorated.__name__ == 'my_name'
