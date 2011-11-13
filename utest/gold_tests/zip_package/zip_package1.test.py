import sys

test.summary='''
This test checks that ZipPackage works correctly
'''
test.copy_directory='zip_package1'

t=test.AddBuildRun('all', '.')
t.disk.file("install.zip", exists = True)
