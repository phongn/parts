import sys

test.summary='''
This tests that resource compiler executes successfully when its command line exceeds 2 kb
'''
if sys.platform == 'win32':
    test.copy_directory='rc_long_cmd'

    t = test.AddBuildRun('all')
    t.returncode = 0
