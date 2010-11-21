test.summary='''
This test that a single REQ.item is mapped correctly. bug was that it is not turned into a REQ set correctly
'''
test.copy_directory='depend4'

t=test.AddBuildRun('all','--verbose=gtest')
t.streams.stdverbose='gold/depend4.gold'
