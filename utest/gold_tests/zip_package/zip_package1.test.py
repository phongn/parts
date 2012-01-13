import sys

test.summary='''
This test checks that ZipPackage adds files to zip if package names are specified
'''
test.copy_directory='zip_package1'

t=test.AddBuildRun('all', '.')

extension = '.exe' if sys.platform=='win32' else ''
contains = ['bin/test1' + extension, 'bin/test2' + extension]
content_tester = t.disk.getDefaultZipTester("install.zip", contains = contains)
t.returncode = 0
t.disk.file("install.zip", exists = True, content_testers = [content_tester])
