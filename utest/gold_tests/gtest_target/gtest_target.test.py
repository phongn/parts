import sys

t=test.AddTestRun()
t.cmd="scons --target-platform=x86 --verbose=gtest_target"
t.returncode=0
if sys.platform == 'win32':
    t.streams.stdverbose='testcase.gold'
else:
    pass

test.AddUpdateCheck()