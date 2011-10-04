test.summary='''
Basic test for making sure sample works
'''
import sys

test.copy_directory=TestSample('unit_test2')

test.AddBuildRun()
test.AddUpdateCheck()
test.AddOutOfDateCheck('utest::')
test.AddCleanRun()
t=test.AddBuildRun("utest::")
if sys.platform=='win32':
    t.disk.file("install/bin/engine.unit_tests-test_2.0.33.exe",exists=False)
    t.disk.file("install/bin/engine.unit_tests-test2_2.0.33.exe",exists=False)
else:
    t.disk.file("install/bin/engine.unit_tests-test_2.0.33",exists=False)
    t.disk.file("install/bin/engine.unit_tests-test2_2.0.33",exists=False)

test.AddUpdateCheck('utest::')
    
test.AddOutOfDateCheck()
