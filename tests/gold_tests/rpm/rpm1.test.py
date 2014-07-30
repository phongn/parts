import sys

Test.Summary=='''
This test checks that the RPM builder adds files to RPM package from SConstruct.
Test for various archive packages along with dpkg 
'''

Test.SkipUnless(
    Condition.HasProgram(
        program= 'rpmbuild',
        msg='Need to have rpmbuild tool on system to build the package',
    )
)

Setup.Copy.FromDirectory('rpm_test1')

Test.AddBuildRun('.')
