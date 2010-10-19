test.summary='''
This test the --build_config cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=test.AddTestRun("good")
t.cmd="scons all --build-config=debug --trace=build_config_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/config_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --buildconfig=debug --trace=build_config_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/config_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --bldcfg=debug --trace=build_config_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/config_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --bcfg=debug --trace=build_config_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/config_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --cfg=debug --trace=build_config_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/config_good1.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --cfg=fakeconfig --trace=build_config_option --tc=null --console-stream=none"
t.returncode=2
t.streams.stdtrace='gold/config_bad1t.gold'
t.streams.stderr='gold/config_bad1e.gold'

