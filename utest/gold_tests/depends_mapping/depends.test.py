test.summary='''
This tests that the mapping of random data work as expected
'''
test.copy_directory='depend1'

t=test.AddBuildRun('all','--verbose=gtest')
