import sys

test.summary='''
This test checks that ZipPackage does not add files if no package name specified
'''
test.copy_directory='zip_package5'

t=test.AddBuildRun('all', '.')
t.returncode = 0
t.disk.file("install.zip", exists = True, size = 0)
