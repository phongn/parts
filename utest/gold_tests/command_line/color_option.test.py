test.summary='''
This test the --color cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
test.copy_directory=TestTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=test.AddTestRun("good")
t.cmd="scons all --color --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=True --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=1 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=yes --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=default --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=darkbg --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=full --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good1.gold'

t=test.AddTestRun("good")
t.cmd="scons all --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good2.gold'

t=test.AddTestRun("good")
t.cmd="scons all --use-color=simple --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good3.gold'

# stdout 
t=test.AddTestRun("stdout")
t.cmd="scons all --use-color=stdout=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdout.gold'

t=test.AddTestRun("stdout")
t.cmd="scons all --use-color=o=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdout.gold'

t=test.AddTestRun("stdout")
t.cmd="scons all --use-color=out=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdout.gold'

 # console
t=test.AddTestRun("console")
t.cmd="scons all --use-color=con=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_console.gold'

t=test.AddTestRun("console")
t.cmd="scons all --use-color=tty=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_console.gold'

t=test.AddTestRun("console")
t.cmd="scons all --use-color=console=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_console.gold'

#stderr
t=test.AddTestRun("stderr")
t.cmd="scons all --use-color=stderr=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stderr.gold'

t=test.AddTestRun("stderr")
t.cmd="scons all --use-color=error=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stderr.gold'

t=test.AddTestRun("stderr")
t.cmd="scons all --use-color=err=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stderr.gold'

t=test.AddTestRun("stderr")
t.cmd="scons all --use-color=e=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stderr.gold'

#stdwrn
t=test.AddTestRun("stdwrn")
t.cmd="scons all --use-color=stdwrn=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdwrn.gold'

t=test.AddTestRun("stdwrn")
t.cmd="scons all --use-color=warning=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdwrn.gold'

t=test.AddTestRun("stdwrn")
t.cmd="scons all --use-color=wrn=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdwrn.gold'

t=test.AddTestRun("stdwrn")
t.cmd="scons all --use-color=w=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdwrn.gold'

#stdmsg
t=test.AddTestRun("stdmsg")
t.cmd="scons all --use-color=stdmsg=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdmsg.gold'

t=test.AddTestRun("stdmsg")
t.cmd="scons all --use-color=message=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdmsg.gold'

t=test.AddTestRun("stdmsg")
t.cmd="scons all --use-color=msg=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdmsg.gold'

t=test.AddTestRun("stdmsg")
t.cmd="scons all --use-color=m=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdmsg.gold'

#stdverbose
t=test.AddTestRun("stdverbose")
t.cmd="scons all --use-color=stdverbose=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdverbose.gold'

t=test.AddTestRun("stdverbose")
t.cmd="scons all --use-color=verbose=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdverbose.gold'

t=test.AddTestRun("stdverbose")
t.cmd="scons all --use-color=ver=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdverbose.gold'

t=test.AddTestRun("stdverbose")
t.cmd="scons all --use-color=v=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdverbose.gold'

#stdtrace
t=test.AddTestRun("stdtrace")
t.cmd="scons all --use-color=stdtrace=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdtrace.gold'

t=test.AddTestRun("stdtrace")
t.cmd="scons all --use-color=trace=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdtrace.gold'

t=test.AddTestRun("stdtrace")
t.cmd="scons all --use-color=t=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_stdtrace.gold'

#color tests
#black
t=test.AddTestRun("black")
t.cmd="scons all --use-color=t=0 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_black.gold'

t=test.AddTestRun("black")
t.cmd="scons all --use-color=t=black --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_black.gold'

t=test.AddTestRun("black")
t.cmd="scons all --use-color=t=blk --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_black.gold'

#red
t=test.AddTestRun("red")
t.cmd="scons all --use-color=t=1 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_red.gold'

t=test.AddTestRun("red")
t.cmd="scons all --use-color=t=red --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_red.gold'

t=test.AddTestRun("red")
t.cmd="scons all --use-color=t=r --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_red.gold'

#green
t=test.AddTestRun("green")
t.cmd="scons all --use-color=t=2 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_green.gold'

t=test.AddTestRun("green")
t.cmd="scons all --use-color=t=green --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_green.gold'

t=test.AddTestRun("green")
t.cmd="scons all --use-color=t=g --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_green.gold'

#yellow
t=test.AddTestRun("yellow")
t.cmd="scons all --use-color=t=3 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_yellow.gold'

t=test.AddTestRun("yellow")
t.cmd="scons all --use-color=t=yellow --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_yellow.gold'

t=test.AddTestRun("yellow")
t.cmd="scons all --use-color=t=y --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_yellow.gold'

#blue
t=test.AddTestRun("blue")
t.cmd="scons all --use-color=t=4 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_blue.gold'

t=test.AddTestRun("blue")
t.cmd="scons all --use-color=t=blue --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_blue.gold'

t=test.AddTestRun("blue")
t.cmd="scons all --use-color=t=b --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_blue.gold'

#purple
t=test.AddTestRun("purple")
t.cmd="scons all --use-color=t=5 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_purple.gold'

t=test.AddTestRun("purple")
t.cmd="scons all --use-color=t=purple --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_purple.gold'

t=test.AddTestRun("purple")
t.cmd="scons all --use-color=t=magenta --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_purple.gold'

t=test.AddTestRun("purple")
t.cmd="scons all --use-color=t=p --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_purple.gold'

t=test.AddTestRun("purple")
t.cmd="scons all --use-color=t=m --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_purple.gold'

#aqua
t=test.AddTestRun("aqua")
t.cmd="scons all --use-color=t=6 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_aqua.gold'

t=test.AddTestRun("aqua")
t.cmd="scons all --use-color=t=aqua --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_aqua.gold'

t=test.AddTestRun("aqua")
t.cmd="scons all --use-color=t=cyan --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_aqua.gold'

t=test.AddTestRun("aqua")
t.cmd="scons all --use-color=t=a --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_aqua.gold'

t=test.AddTestRun("aqua")
t.cmd="scons all --use-color=t=c --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_aqua.gold'

#white
t=test.AddTestRun("white")
t.cmd="scons all --use-color=t=7 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_white.gold'

t=test.AddTestRun("white")
t.cmd="scons all --use-color=t=white --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_white.gold'

t=test.AddTestRun("white")
t.cmd="scons all --use-color=t=lightgray --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_white.gold'

t=test.AddTestRun("white")
t.cmd="scons all --use-color=t=lightgrey --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_white.gold'

t=test.AddTestRun("white")
t.cmd="scons all --use-color=t=w --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_white.gold'

t=test.AddTestRun("white")
t.cmd="scons all --use-color=t=lg --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_white.gold'

#gray
t=test.AddTestRun("gray")
t.cmd="scons all --use-color=t=8 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_gray.gold'

t=test.AddTestRun("gray")
t.cmd="scons all --use-color=t=gray --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_gray.gold'

t=test.AddTestRun("gray")
t.cmd="scons all --use-color=t=grey --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_gray.gold'

#bright red
t=test.AddTestRun("brightred")
t.cmd="scons all --use-color=t=9 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightred.gold'

t=test.AddTestRun("brightred")
t.cmd="scons all --use-color=t=brightred --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightred.gold'

t=test.AddTestRun("brightred")
t.cmd="scons all --use-color=t=br --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightred.gold'

#bright green
t=test.AddTestRun("brightgreen")
t.cmd="scons all --use-color=t=10 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightgreen.gold'

t=test.AddTestRun("brightgreen")
t.cmd="scons all --use-color=t=brightgreen --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightgreen.gold'

t=test.AddTestRun("brightgreen")
t.cmd="scons all --use-color=t=bg --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightgreen.gold'

#bright yellow
t=test.AddTestRun("brightyellow")
t.cmd="scons all --use-color=t=11 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightyellow.gold'

t=test.AddTestRun("brightyellow")
t.cmd="scons all --use-color=t=brightyellow --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightyellow.gold'

t=test.AddTestRun("brightyellow")
t.cmd="scons all --use-color=t=by --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightyellow.gold'

#bright blue
t=test.AddTestRun("brightblue")
t.cmd="scons all --use-color=t=12 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightblue.gold'

t=test.AddTestRun("blue")
t.cmd="scons all --use-color=t=brightblue --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightblue.gold'

t=test.AddTestRun("blue")
t.cmd="scons all --use-color=t=bb --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightblue.gold'

#bright purple
t=test.AddTestRun("brightpurple")
t.cmd="scons all --use-color=t=13 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightpurple.gold'

t=test.AddTestRun("brightpurple")
t.cmd="scons all --use-color=t=brightpurple --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightpurple.gold'

t=test.AddTestRun("brightpurple")
t.cmd="scons all --use-color=t=brightmagenta --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightpurple.gold'

t=test.AddTestRun("brightpurple")
t.cmd="scons all --use-color=t=bm --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightpurple.gold'

t=test.AddTestRun("brightpurple")
t.cmd="scons all --use-color=t=bp --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightpurple.gold'

#bright aqua
t=test.AddTestRun("brightaqua")
t.cmd="scons all --use-color=t=14 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightaqua.gold'

t=test.AddTestRun("brightaqua")
t.cmd="scons all --use-color=t=brightaqua --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightaqua.gold'

t=test.AddTestRun("brightaqua")
t.cmd="scons all --use-color=t=brightcyan --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightaqua.gold'

t=test.AddTestRun("brightaqua")
t.cmd="scons all --use-color=t=ba --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightaqua.gold'

t=test.AddTestRun("brightaqua")
t.cmd="scons all --use-color=t=bc --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightaqua.gold'

#bright white
t=test.AddTestRun("brightwhite")
t.cmd="scons all --use-color=t=15 --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightwhite.gold'

t=test.AddTestRun("brightwhite")
t.cmd="scons all --use-color=t=brightwhite --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightwhite.gold'

t=test.AddTestRun("brightwhite")
t.cmd="scons all --use-color=t=bw --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_brightwhite.gold'

#default
t=test.AddTestRun("default")
t.cmd="scons all --use-color=t=default --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_default.gold'

#bright
t=test.AddTestRun("bight")
t.cmd="scons all --use-color=t=bright --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_bold.gold'

t=test.AddTestRun("bight")
t.cmd="scons all --use-color=t=bold --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_bold.gold'

#dim
t=test.AddTestRun("dim")
t.cmd="scons all --use-color=t=dim --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_dim.gold'

#mass set
t=test.AddTestRun("good")
t.cmd="scons all --use-color=c=r:g,o=y:b,e=g:br,w=3:4,m=10:13,v=bold:default,t=blk:white --trace=use_color_option --tc=null --console-stream=none"
t.returncode=0
t.streams.stdtrace='gold/color_good4.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --use-color=foo --trace=use_color_option --tc=null --console-stream=none"
t.returncode=2
t.streams.stderr='gold/color_bad1.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --use-color=c=r:g,o=y,b:e=g:br,w=3:4,m=10:13,v=bold:default,t=blk:white --trace=use_color_option --tc=null --console-stream=none"
t.returncode=2
t.streams.stderr='gold/color_bad2.gold'

t=test.AddTestRun("bad")
t.cmd="scons all --use-color=stdout=badcolor --trace=use_color_option --tc=null --console-stream=none"
t.returncode=2
t.streams.stderr='gold/color_bad3.gold'

