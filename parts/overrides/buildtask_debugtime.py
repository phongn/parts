'''
We monkey-patch SCons.Script.Main.BuildTask.execute() method to make sure commad execution
time statistics are gathered for all commands, even for those ending in some kind of
exception. So actual patch is "wrapping the call to SCons.Taskmaster.OutOfDateTask.execute()
with try..finally", all the code is taken as-is from SCons 2.1.
'''

import SCons.Script.Main as Main
import SCons.Taskmaster

import time
import sys

def patched_execute(self):
    if Main.print_time:
        start_time = time.time()
        if Main.first_command_start is None:
            Main.first_command_start = start_time
    try:
        SCons.Taskmaster.OutOfDateTask.execute(self)
    finally:
        if Main.print_time:
            finish_time = time.time()
            Main.last_command_end = finish_time
            Main.cumulative_command_time += finish_time - start_time
            sys.stdout.write("Command execution time: %f seconds\n" % (finish_time - start_time))

Main.BuildTask.execute = patched_execute