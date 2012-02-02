import sys

test.summary='''
This test checks that ZipPackage does not add files if no_pkg is specified
'''
test.copy_directory='zip_package2'

t=test.AddBuildRun('all', '.')

extension = '.exe' if sys.platform=='win32' else ''
contains = ['bin/test1' + extension]
notContains = ['bin/test2' + extension]
content_tester = t.disk.getDefaultZipTester("install.zip", contains = contains, notContains = notContains)
t.returncode = 0
t.disk.file("install.zip", exists = True, content_testers = [content_tester])
