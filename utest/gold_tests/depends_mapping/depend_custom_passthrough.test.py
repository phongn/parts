test.summary='''
This tests that the mapping of custom data work as expected in classic format, when mapped to public area
'''
test.copy_directory='depend3'

t=test.AddBuildRun('all','--verbose=gtest')
t.streams.stdverbose='gold/depend3.gold'
