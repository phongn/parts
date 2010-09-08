test.summary='''
This test the --ccopy_logic cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly

t=test.AddTestRun("good")
t.cmd="scons all --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good0.gold'

t=test.AddTestRun("good")
t.cmd="scons all --ccopy-logic=copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --copy-logic=copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --ccopy=copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good1.gold'

# test differ cases of 'hard-soft-copy','soft-hard-copy','soft-copy','hard-copy','copy'
t=test.AddTestRun("good")
t.cmd="scons all --ccopy=hard-soft-copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --ccopy=soft-hard-copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --ccopy=soft-copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good4.gold'

t=test.AddTestRun("good")
t.cmd="scons all --ccopy=hard-copy --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/ccopy_good5.gold'

#error cases

t=test.AddTestRun("bad")
t.cmd="scons all --ccopy-logic=hard --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=2
t.streams.stderr='gold/ccopy_bad1.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --ccopy-logic=copy,foo --trace=ccopy_logic_option --tc=null --hide-progress"
t.returncode=2
t.streams.stderr='gold/ccopy_bad2.gold'

