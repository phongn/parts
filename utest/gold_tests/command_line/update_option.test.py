test.summary='''
This test the --update cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=test.AddTestRun("good")
t.cmd="scons all --update=auto --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=auto --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=true --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=yes --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=t --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=all --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=False --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=no --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=f --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=none --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --vcs-update=joe,foo,boo --trace=update_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/update_good4.gold'
