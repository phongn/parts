test.summary='''
This tests use of default with nodes in it
'''

test.copy_directory='default'

t=test.AddTestRun("good")
t.cmd="scons --console-stream=none"
t.returncode=0
