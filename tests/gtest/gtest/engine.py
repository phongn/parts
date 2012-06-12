import os
import shutil
import test
import runtesttask
import setup
import host
import glb
import testers
from common.pathutils import remove_read_only


class Engine(object):
    """description of class"""

    def __init__(self,host,jobs=1,test_dir='./',run_dir="./_sandbox",gtest_site=None):
        self.__host=host
        self.__tests={}
        self.__jobs=jobs
        self.__test_dir=test_dir
        self.__run_dir=os.path.abspath(run_dir)
        self.__gtest_site=gtest_site
        if glb.Engine:
            raise RuntimeError("Only one engine can be created at a time")
        glb.Engine=self
       
    #def __del__(self):
        #glb.Engine=None

    def Start(self):
        if os.path.exists(self.__run_dir):
            host.WriteVerbose("engine","The Sandbox directory exists, will try to remove")
            try:
                shutil.rmtree(self.__run_dir,onerror=remove_read_only)
            except Exception, e:
                host.WriteError("Unable to remove sandbox directory for clean test run\n Reason: {0}".format(e),show_stack=False)
            host.WriteVerbose("engine","The Sandbox directory was removed")
        host.WriteVerbose("engine","Loading Extensions")
        self._load_extensions()
        host.WriteVerbose("engine","Scanning for tests")
        self._scan_for_tests()
        host.WriteVerbose("engine","Running tests")
        self._run_tests()
        host.WriteVerbose("engine","Making report")
        ret=self._make_report()
        return ret

    def _load_extensions(self):
        # load files of our extension type in the directory

        locals={
                'AddTestRunSet':test.AddTestRunSet,
                'AddSetupTask':setup.AddSetupTask,
                'SetupTask':setup.SetupTask,
                }
        if self.__gtest_site is None:
            path=os.path.join(self.__test_dir,'gtest-site')
        else:
            path=os.path.abspath(self.__gtest_site)
        if os.path.exists(path):
            host.WriteVerbose("engine","Loading Extensions from {0}".format(path))
            for f in os.listdir(path):
                f=os.path.join(path,f)
                if os.path.isfile(f) and f.endswith("test.ext"):
                    self._load_file(f,locals,locals)
        else:
            host.WriteVerbose("engine","gtest-site path not found")
        


    def _scan_for_tests(self):
        
        ret=[]
        for root, dirs, files in os.walk(self.__test_dir):
            host.WriteVerbose("test_scan","Looking for tests in",root)
            
            for f in files:
                if f.endswith('.test.py') or f.endswith(".test"):
                    if f.endswith('.test.py'):
                        name=f[:-len('.test.py')]
                    else:
                        name=f[:-len('.test')]

                    if self.__tests.has_key(name):
                        host.WriteWarning("overiding test",name, "with test in", root)
                    host.WriteVerbose("test_scan","   Found test",name)
                    self.__tests[name]=test.Test(name,root,f,self.__run_dir,self.__test_dir)

    def _run_tests(self):
        for t in self.__tests.itervalues():
            tmp=runtesttask.RunTestTask(t)
            tmp()
    
    def _load_file(self,file,globals=None,locals=None):
        g = globals if globals else {}
        l = locals if locals else {}
        host.WriteVerbose("engine","Loading file: {0}",file)
        exec(compile(open(file).read(), file, 'exec'),g,l)
        #print g
        

    def _make_report(self):
        host.WriteMessage("\nReport: --------------")
        # fix this up to use an report object
        had_issue=0
        skipped=0
        def print_run_result(i):
            if i.Result == testers.ResultType.Passed:
                host.WriteMessage("  Test: {0} - {1}".format(i.Description,testers.ResultType.to_string(i.Result)))
            else:
                host.WriteMessage("  Test: {0} - {1}".format(i.Description,testers.ResultType.to_string(i.Result)))
                host.WriteMessage("   Reason: {0}".format(i.Reason))

        for t in self.__tests.itervalues():
            if t._Result == testers.ResultType.Skipped:
                skipped+=1
                host.WriteMessage('\nTest run "{0}" in directory "{1}"'.format(t.TestFile,t.TestDirectory))
                host.WriteMessage(" Skipped - {0}".format(t._Conditions._Reason))
            elif t._Result != testers.ResultType.Passed:
                had_issue+=1
                host.WriteMessage('\nTest run "{0}" in directory "{1}"'.format(t.TestFile,t.TestDirectory))
                
                if t.Setup._Failed:
                    host.WriteMessage(" Setup: - Failed")
                    host.WriteMessage("   Reason: {0}".format(t.Setup._Reason))
                for tr in t._TestRuns:
                    if tr._Result == testers.ResultType.Passed:
                        host.WriteMessage("\n {0} - Passed".format(tr.Name))
                    elif tr._Result == testers.ResultType.Warning:
                        host.WriteMessage("\n {0} - Warning".format(tr.Name))
                        for i in tr.get_testers():
                            print_run_result(i)
                    elif tr._Result == testers.ResultType.Failed:
                        host.WriteMessage("\n {0} - Failed".format(tr.Name))
                        for i in tr.get_testers():
                            print_run_result(i)
                    elif tr._Result == testers.ResultType.Skipped:
                        host.WriteMessage("\n {0} - Skipped".format(tr.Name))
                        host.WriteMessage("  Reason: Previous test run failed.".format())
                    elif tr._Result == testers.ResultType.Unknown:
                        host.WriteMessage("\n {0} - Unknown?".format(tr.Name))
                        for i in tr.get_testers():
                            print_run_result(i)

        host.WriteMessage("")
        if not had_issue:
            host.WriteMessage("All tests passed!\n Warnings: 0\n Skipped: {0}".format(skipped))
        else:
            host.WriteMessage("Test run had Failures\n Errors: {0}\n Warnings: 0\n Skipped: {1}".format(had_issue,skipped))

        if had_issue:
            return 1
        return 0


    @property
    def Host(self):
        return self.__host

   



        
    