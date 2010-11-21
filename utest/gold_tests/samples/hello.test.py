test.summary='''
Basic test for making sure sample works
'''

test.copy_directory=TestSample('hello')


test.AddOutOfDateCheck()

t=test.AddBuildRun()

test.AddUpdateCheck()
test.AddCleanRun()
test.AddOutOfDateCheck()

