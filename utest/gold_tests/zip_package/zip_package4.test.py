import sys

test.summary='''
This test checks that ZipPackage adds only files with matching package names
'''
test.copy_directory='zip_package4'

t=test.AddBuildRun('all', '.')
t.returncode = 0
t.disk.file("install.zip", exists = True, size = 0)
