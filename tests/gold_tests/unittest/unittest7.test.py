Test.Summary='''
Test that run_utest:: targets output is put into separate log file.
'''
import os
import platform
import sys

def getSystemName():
    PLATFORM_MAP = {'windows': 'win32',
                    'linux':   'posix',
                    'mac':     'darwin'}
    systemName = platform.system().lower()
    return PLATFORM_MAP.get(systemName, systemName)

Setup.Copy.FromDirectory('test7')

# generate gold files on-the-fly
for quote, name in (('', 'noquote'), ('"', 'quote')):
    with open(str(test.TestDirectory) + '/unittest7runutest-{0}.log'.format(name), 'w') as gold:
        gold.write('''Task:{quote}cd _unit_tests{sep}debug_{os}-x86{sep}root.utest_1.0.0{sep}test && ..{sep}..{sep}..{sep}..{sep}_install{sep}debug_{os}-x86_default{sep}bin{sep}root.utest-test_1.0.0{quote}
Output begin ----------------------------------------------------------------
Output end   ----------------------------------------------------------------
return code = 1
'''.format(sep=os.sep, os=getSystemName(), quote=quote))
    with open(str(test.TestDirectory)+'/unittest7runutest1-{0}.log'.format(name), 'w') as gold:
        gold.write('''Task:{quote}cd _unit_tests{sep}debug_{os}-x86{sep}root.utest_1.0.0{sep}test1 && ..{sep}..{sep}..{sep}..{sep}_install{sep}debug_{os}-x86_default{sep}bin{sep}root.utest-test1_1.0.0{quote}
Output begin ----------------------------------------------------------------
Output end   ----------------------------------------------------------------
return code = 1
'''.format(sep=os.sep, os=getSystemName(), quote=quote))

# run test.. should not have any failures
t = Test.AddBuildRun('run_utest:: -j3 TARGET_ARCH=x86')
t.ReturnCode = 0
f = t.Disk.File('logs/run_utest.root.utest-test_1.0.0{suffix}.log'.\
                format(suffix='.exe' if platform.system().lower() == 'windows' else ''))
f.Exists = True
f.Content = ['unittest7runutest-noquote.log', 'unittest7runutest-quote.log']

f = t.Disk.File('logs/run_utest.root.utest-test1_1.0.0{suffix}.log'.format(suffix='.exe' if platform.system().lower() == 'windows' else ''))
f.Exists = True
f.Content = ['unittest7runutest1-noquote.log', 'unittest7runutest1-quote.log']

