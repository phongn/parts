test.summary='''
This tests some init behavior in the node that was found to cause stack overflow.
'''

test.copy_directory='recursiondepthbug'

t=test.AddTestRun("setup")
t.cmd="cd utest && scons --console-stream=none"
t.returncode=0

# the second pass should build
t=test.AddTestRun()
t.cmd="cd utest && scons --console-stream=none"
t.returncode=0

