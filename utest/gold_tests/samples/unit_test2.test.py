test.summary='''
Basic test for making sure sample works
'''

test.copy_directory=TestSample('unit_test2')

test.AddBuildRun()
test.AddUpdateCheck()
test.AddOutOfDateCheck('utest::')
test.AddCleanRun()
test.AddBuildRun("utest::")
test.AddUpdateCheck('utest::')
test.AddOutOfDateCheck()
