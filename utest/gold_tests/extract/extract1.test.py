import sys

test.summary='''
This test checks that Extract works correctly
'''
test.copy_directory='extract1'

t = test.AddBuildRun('all')
t.returncode = 0
if sys.platform=='win32':
    t.disk.file("install/bin/test.exe", exists = True)
else:
    t.disk.file("install/bin/test", exists = True)
