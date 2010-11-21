test.summary='''
Basic test for making sure sample works
'''

test.copy_directory=TestSample('unit_test1')

t=test.AddBuildRun("all")
t=test.AddBuildRun("utest::")
test.AddUpdateCheck('utest::')

