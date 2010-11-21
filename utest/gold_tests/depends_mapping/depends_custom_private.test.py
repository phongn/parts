test.summary='''
This tests that the mapping of custom data work as expected in classic format
'''
test.copy_directory='depend1'

t=test.AddBuildRun('all','--verbose=gtest')
t.streams.stdverbose='gold/depend1.gold'
