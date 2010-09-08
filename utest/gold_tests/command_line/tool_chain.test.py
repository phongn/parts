test.summary='''
This test the --tool_chain cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

t=test.AddTestRun("good")
t.cmd="scons all --tool-chain=null --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --toolchain=null --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null_1.3.4 --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null_1. --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null_ --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good4.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null,null --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good5.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null_1,null --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good6.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null_1,null_1 --trace=tool_chain_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/tc_good7.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --tc=foo --trace=tool_chain_option --hide-progress"
t.returncode=2
t.streams.stderr='gold/tc_bad1.gold'
