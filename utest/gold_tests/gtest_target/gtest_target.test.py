import sys

test.cmd="scons --target-platform=x86 --verbose=gtest_target"
test.returncode=None
if sys.platform == 'win32':
    test.streams.stdverbose='testcase.gold'
else:
    pass    