Test.Summary = '''
A CMake() build with a Ninja generator configures once. The second build of
an unchanged tree must not run the configure step again. The generator is
"Ninja Multi-Config", whose name has a space, so it also checks that the name
reaches cmake as a single -G argument.
'''

Test.SkipUnless(
    Condition.HasProgram('cmake', 'cmake is required to run this build'),
    Condition.HasProgram('ninja', 'ninja is required to run this build'),
)

Setup.Copy.FromDirectory('cmake_ninja')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = Testers.ContainsExpression(r'-G "Ninja Multi-Config"', 'the first build configures with Ninja Multi-Config')

t = Test.AddBuildRun('all')
t.ReturnCode = 0
t.Streams.stdout = Testers.ExcludesExpression(r'-G "Ninja Multi-Config"', 'the second build does not configure again')
