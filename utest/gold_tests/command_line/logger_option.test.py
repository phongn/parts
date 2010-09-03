test.summary='''
This test the --log cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=test.AddTestRun("good")
t.cmd="scons all --log --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=text --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=True --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=yes --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=1 --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=html --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=False --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good4.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=none --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good4.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=0 --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good4.gold'

t=test.AddTestRun("good")
t.cmd="scons all --log=no --trace=logger_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/log_good4.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --log=foo --trace=logger_option --tc=null --hide-progress"
t.returncode=2
t.streams.stderr='gold/log_bad1.gold'


