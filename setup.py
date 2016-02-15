import sys

try:
    import paver.tasks
except ImportError:
    from os.path import exists
    if exists("paver-minilib.zip"):
        sys.path.insert(0, "paver-minilib.zip")
    import paver.tasks

sys.argv.insert(1, 'setup_options')
paver.tasks.main()
