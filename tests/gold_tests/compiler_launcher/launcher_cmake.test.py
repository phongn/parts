Test.Summary = '''
CC_LAUNCHER and CXX_LAUNCHER wrap the compiles of a native build, including
one whose commands go through a response file, and of a CMake() build.
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
log.Content = Testers.ContainsExpression(r'native\.c', 'the native C compile went through CC_LAUNCHER')
log.Content += Testers.ContainsExpression(r'native_cxx\.cpp', 'the native C++ compile went through CXX_LAUNCHER')
# MAXLINELENGTH=20 puts the whole compile in a response file; the launcher has
# to stay on the command line in front of the compiler and its @file
log.Content += Testers.ContainsExpression(r' @\S', 'the response-file compile went through CC_LAUNCHER')
log.Content += Testers.ContainsExpression(r'cmake_main\.c', 'the CMake C compile went through CC_LAUNCHER')
log.Content += Testers.ContainsExpression(r'cmake_cxx\.cpp', 'the CMake C++ compile went through CXX_LAUNCHER')
