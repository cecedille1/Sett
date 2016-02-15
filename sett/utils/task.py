# -*- coding: utf-8 -*-


def task_name(name):
    """
    Set the name of the task

    >>> @task
    >>> @task_name('django')
    >>> def django_task():
    ...     pass
    >>> environment.get_task('django')
    """
    def decorator(fn):
        fn.__name__ = name
        return fn
    return decorator
