import sys
test.summary='''
Test that the REQ.EXISTS works as expected
'''
test.copy_directory='depend5'

t=test.AddBuildRun('part2')

if sys.platform=='win32':
    t.disk.file("install/debug_win32-x86_64/bin/a1.exe",exists=True)
    t.disk.file("install/debug_win32-x86_64/bin/a2.exe",exists=True)
else:
    t.disk.file("install/debug_win32-x86_64/bin/a1",exists=True)
    t.disk.file("install/debug_win32-x86_64/bin/a2",exists=True)

test.AddUpdateCheck('part2')
t=test.AddCleanRun('part2')
if sys.platform=='win32':
    t.disk.file("install/debug_win32-x86_64/bin/a1.exe",exists=False)
    t.disk.file("install/debug_win32-x86_64/bin/a2.exe",exists=False)
else:
    t.disk.file("install/debug_win32-x86_64/bin/a1",exists=False)
    t.disk.file("install/debug_win32-x86_64/bin/a2",exists=False)
