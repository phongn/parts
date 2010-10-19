test.summary='''
This test the basic ability to create a new entry and save it
'''
test.copy_directory=TestTemplate('empty')

t=test.AddTestRun("good")
t.cmd="scons . --console-stream=none"
t.returncode=0
t.disk.file(".parts.cache/mytestkey/foo.cache",exists=True)

