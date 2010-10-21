test.summary='''
This tests that a basic empty Scons script will run with Parts
'''
# fix this test to verify that the error is what we expect

t=test.AddTestRun("good")
t.cmd="scons . --console-stream=none"
t.returncode=2


