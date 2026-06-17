Test.Summary = '''
CC_LAUNCHER wraps the C compile of a native build and of a CMake() build.
launch.sh logs each command it runs, so the log shows which compiles went
through it.
'''

Test.SkipUnless(
    Condition.HasProgram('cmake', 'cmake is required to run this build'),
)

Setup.Copy.FromDirectory('launcher_cmake')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
log = t.Disk.File('launch.log', exists=True)
log.Content = Testers.ContainsExpression(r'native\.c', 'the native compile went through CC_LAUNCHER')
log.Content += Testers.ContainsExpression(r'cmake_main\.c', 'the CMake compile went through CC_LAUNCHER')
