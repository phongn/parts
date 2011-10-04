test.summary='''
This test a the different load logic cases with a part that does not depend on its sub-parts
'''

test.copy_directory=TestTemplate('independent_subparts')

t=test.AddTestRun("build-all")
t.cmd="scons --console-stream=none all"
t.returncode=0

test.AddUpdateCheck()
test.AddCleanRun()
test.AddOutOfDateCheck()

t=test.AddTestRun("build-target")
t.cmd="scons --console-stream=none A --ll=all"
t.returncode=0

test.AddUpdateCheck('A')
test.AddOutOfDateCheck('A.sub1')
test.AddOutOfDateCheck('A.sub2')
test.AddOutOfDateCheck('A.sub3')

t=test.AddTestRun("build-target-target")
t.cmd="scons --console-stream=none A:: --ll=target"
t.returncode=0

test.AddUpdateCheck()
test.AddCleanRun()

t=test.AddTestRun("build-target-min")
t.cmd="scons --console-stream=none A:: --ll=min"
t.returncode=0

test.AddUpdateCheck()
test.AddCleanRun()

t=test.AddTestRun("build-target-unsafe")
t.cmd="scons --console-stream=none A:: --ll=unsafe"
t.returncode=0

test.AddUpdateCheck()
test.AddCleanRun()
