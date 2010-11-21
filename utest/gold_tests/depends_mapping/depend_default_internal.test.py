test.summary='''
Test that the REQ.default(internal=True) works as expected
'''
test.copy_directory='depend6'

t=test.AddBuildRun('all','--verbose=gtest')
t.streams.stdverbose='gold/depend6.gold'
