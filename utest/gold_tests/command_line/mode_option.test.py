test.summary='''
This test the --mode cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=test.AddTestRun("good")
t.cmd="scons all --mode=foo --trace=mode_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/mode_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --trace=mode_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/mode_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --mode=foo,boo --trace=mode_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/mode_good3.gold'
