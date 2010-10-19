test.summary='''
This test case tests that depends on maps and part with no version to a range of *
Test cases give reported as a bug.. used as make sure regression does not happen
'''
test.copy_directory='partsbug'

t=test.AddTestRun()
t.cmd="scons . --console-stream=none"
t.returncode=0
