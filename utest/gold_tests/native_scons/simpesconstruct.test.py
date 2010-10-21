test.summary='''
This tests that a basic empty Scons script will run with Parts
'''


t=test.AddTestRun("good")
t.cmd="scons . --console-stream=none"
t.returncode=0


