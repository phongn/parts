import os

Test.Summary='''
This test checks that extract is OK from repository created on the fly
'''

# Setup
Test.Setup.Copy.FromDirectory('checkout1')
Test.Setup.Svn.CreateRepository('repo_checkout1')
Test.Setup.Svn.ImportDirectory('repo_checkout1','checkout1/repo')


# Configuration of test run(s)
t = Test.AddBuildRun('all', 'SVN_SERVER=$REPO_CHECKOUT1_SVN_PATH')
t.ReturnCode = 0
