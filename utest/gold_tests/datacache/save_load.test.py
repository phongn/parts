test.summary='''
This test the basic ability to create a new entry and save it and then load it
'''
test.copy_directory=TestTemplate('empty')

t=test.AddBuildRun('.','--verbose=gtest')
t.disk.file(".parts.cache/mytestkey/foo.cache",exists=True)
t.streams.stdverbose='gold/save_load.gold'

# test that if we only load that this works
t=test.AddBuildRun('.','--verbose=gtest load_only=True')
t.streams.stdverbose='gold/save_load.gold'