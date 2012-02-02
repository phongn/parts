import os

test.summary='''
This test checks that extract is OK from repository created on the fly
'''

# Setup
test.setup.copyDirectory('checkout1')
test.setup.createSvnRepository('repo_checkout1', 'repo')

# Configuration of test run(s)
t = test.AddBuildRun('all', 'SVN_SERVER=file:///' + os.path.abspath(os.path.join(test.test_dir, 'repo_checkout1')))
t.returncode = 0
