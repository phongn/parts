test.summary='''
This test the --target_platform cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=test.AddTestRun("good")
t.cmd="scons all --target-platform=win32-x86 --trace=target_platform_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --target=win32-x86 --trace=target_platform_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --target-platform=posix --trace=target_platform_option_os --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --target-platform=x86 --trace=target_platform_option_arch --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good3.gold'

t=test.AddTestRun("good")
t.cmd="scons all --target-platform=hp-ux-x86 --trace=target_platform_option --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good4.gold'

t=test.AddTestRun("good")
t.cmd="scons all --target-platform=hp-ux --trace=target_platform_option_os --tc=null --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good5.gold'

t=test.AddTestRun("good")
t.cmd="scons all --tc=null --trace=target_platform_option --hide-progress"
t.returncode=0
t.streams.stdtrace='gold/target_good6.gold'

# do runs with bad options
t=test.AddTestRun("bad")
t.cmd="scons all --target-platform=fake-x86 --trace=target_platform_option --tc=null"
t.returncode=2
t.streams.stderr='gold/target_bad1.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --target-platform=badval --trace=target_platform_option --tc=null"
t.returncode=2
t.streams.stderr='gold/target_bad2.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --target-platform=darwin-z7000 --trace=target_platform_option --tc=null"
t.returncode=2
t.streams.stderr='gold/target_bad3.gold'

