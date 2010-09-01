import re
import os
import subprocess
import time
import threading
import difflib
import types
import shutil

'''
gtest -- for gold file testing

Expected directory layout

gtest.py
    /<group>
        <test name>.test.py
        sconstruct_<test_name> or sconstruct (or custome value via test.sconstruct_file) this value will be copied to test area as "sconstruct".
                                    If no find it will assume "Sconstruct" is in directory copy ( given there is a copy), else error 
            /<sub_dir contains sample code>

    /templates -- contains command test case structure to help with reuse 
        /<template_name>

'''


cwd_dir=os.path.split(__file__)[0]
test_root=os.path.join(cwd_dir,"_run_sandbox")
parts_path=os.path.abspath(os.path.normpath('../../'))
os.environ['PYTHONPATH']=parts_path


full_stream_file='stream.both.txt'
out_stream_file='stream.out.txt'
err_stream_file='stream.err.txt'
verbose_stream_file='stream.verbose.txt'
trace_stream_file='stream.trace.txt'

if os.path.exists(test_root):
    shutil.rmtree(test_root)

def TestTemplate(name):
    return os.path.join(cwd_dir,'templates',name)    

class Test(object):
    ''' This Define a basic test. A basic test is a set of TestRun
    Each test Run run soem kind of command, and fro each run we can test
    Some state to make sure everything is OK.
    '''
    def __init__(self,name,location):
        #traits
        self.name=name
        self.location=location
        self.run_serial=False
        self.summary=''
        self.sconstruct_file=None
        self.copy_directory=False #true to copy contents of test directory else path of directory to copy
        self.run=[]

    def AddTestRun(self,name='general'):
        tmp=TestRun(self,"%s-%s"%(name,len(self.run)))
        self.run.append(tmp)
        return tmp

    def AddCleanRun(self,target='all'):
        tmp=TestRun(self,"clean-run-%s"%len(self.run))
        tmp.cmd='scons -c %s'%target
        tmp.returncode=0
        self.run.append(tmp)
        return tmp
    
    def AddUpdateCheckSCons(self,target='all'):
        tmp=TestRun(self,"up-to-date-scons-run-%s"%len(self.run))
        tmp.cmd='scons -Q %s --disable-parts-cache'%target
        tmp.returncode=0
        #add stream test
        self.run.append(tmp)
        return tmp
    
    def AddUpdateCheckParts(self,target='all'):
        tmp=TestRun(self,"up-to-date-parts-run-%s"%len(self.run))
        tmp.cmd='scons -Q %s'%target
        tmp.returncode=0
        #add stream test
        self.run.append(tmp)
        return tmp
        
    def AddUOutOfDateCheck(self,target="all"):
        tmp=TestRun(self,"out-of-date-check-run-%s"%len(self.run))
        tmp.cmd='scons -Q %s'%target
        tmp.returncode=1
        #add stream test
        self.run.append(tmp)
        return tmp
        
            

class TestRun(object):
    '''
    A test run allows us to test a certain command and see if certian actions happened as excepted
    Speceial cases of Test run may test it a test is up-to-date, or out-of -date
    '''
    def __init__(self,test,name):
        #required setup
        self.name=name
        self.cmd="" # this is the command we want to run
        
        # possible stuff we can test
        # all cases below None means skip
        self.returncode=None # can be a int
        # time
        self.time=Time()
        self.streams=Stream(test,self)
        self.disk=Disk(self)

class Time(object):
    ''' Allows us to test that something happened within a certain time.
    If we go over the time we can exit the test and say we had a failure
    '''
    def __init__(self):
        self.total=None
        self.interval=None

class Stream(object):
    '''
    this allows us to test against different streams. Parts add "virtual" streams
    As it no really possible to add new streams given modern console logic
    Each stream can be tested against a gold file. By default the stream is diffed with
    the python difflib. However custom diff logic can be setup by setting the <stream>_tester attribute
    '''
    def __init__(self,test,testrun):
        self.test=test
        self.testrun=testrun
        self.stdout=None # only the stdout text
        self.stdout_tester=difflib.context_diff
        self.stderr=None # only the stderr text
        self.stderr_tester=difflib.context_diff
        self.stdverbose=None # filtered data that was outputted to Parts stdverbose
        self.stdverbose_tester=difflib.context_diff
        self.stdtrace=None #filetered data that was outputted to Parts stdtrace
        self.stdtrace_tester=difflib.context_diff
        self.full_stream=None # both stdout ad stderr
        self.full_stream_tester=difflib.context_diff
    
    def _testbase(self,infile,goldfile,tester):
        # Setup data for the test
        fromfile=infile
        tofile=os.path.join(self.test.location,goldfile)
        if os.path.exists(tofile):
            fromlines = open(fromfile, 'U').readlines()
            tolines = open(tofile, 'U').readlines()
        else:
            return "Error File: ["+tofile+"] was not found!"
        
        return "".join(tester(tolines,fromlines,tofile,fromfile))

    
    def TestStdout(self,base):
    
        if self.stdout is None:
            return None
        return self._testbase(os.path.join(base,out_stream_file),
            self.stdout,
            self.stdout_tester)
    
    def TestStderr(self,base):
    
        if self.stderr is None:
            return None
        return self._testbase(os.path.join(base,err_stream_file),
            self.stderr,
            self.stderr_tester)
        
    def TestStdVerbose(self,base):
    
        if self.stdverbose is None:
            return None
        return self._testbase(os.path.join(base,verbose_stream_file),
            self.stdverbose,
            self.stdverbose_tester)
        
    def TestStdTrace(self,base):
    
        if self.stdtrace is None:
            return None
        return self._testbase(os.path.join(base,trace_stream_file),
            self.stdtrace,
            self.stdtrace_tester)
        
    def TestFullStream(self,base):
    
        if self.full_stream is None:
            return None
        return self._testbase(os.path.join(base,full_stream_file),
            self.full_stream,
            self.full_stream_tester)

class File(object):
    '''
    Allows us to test for a file. We can test for size, existance and content
    '''
    def __init__(self,test,name,exists=None,size=None,content=None):
        self.test=test
        self.name=name
        self.exists=None
        self.size=None
        self.content=None
        self.content_tester=difflib.context_diff
        
    def TestSize(self):
        
        # see if we want to test this:
        if self.size is None:
            return None
        
        # open file 
        # seek to get size()
        
        return (self.size==file_size,file_size)
    
    def TestContent(self):
    
        if self.content is None:
            return None
        # Setup data for the test
        fromfile=self.name
        tofile=os.path.join(self.test.location,self.content)
        if os.path.exists(tofile):
            fromlines = open(fromfile, 'U').readlines()
            tolines = open(tofile, 'U').readlines()
        else:
            return "Error File: ["+tofile+"] was not found!"
        
        return "".join(self.content_tester(tolines,fromlines,tofile,fromfile))

        

class Dir(object):
    ''' allow us to test for the existance of a Directory'''
    def __init__(self,name,exists=None):
        self.name=name
        self.exists=exists

class Disk(object):
    '''
    allows use to define what kind of disk based test we want to do
    '''
    def __init__(self,test):
        self.test=test
        self.files=[]
        self.dirs=[]

    def file(self,name,exists=None,size=None,content=None):
        tmp=File(name,exists,size,content)
        self.__dict__[name]=tmp
        self.files.append(File(self.test,name,exists,size,content))

    def dir(self,name,exists=None):
        tmp=Dir(name,exists)
        self.__dict__[name]=tmp
        self.dirs.append(Dir(name,exists))

class TestResult(object):
    def __init__(self,test,testrun):
        self.test=test
        self.testrun=testrun
        self.returncode=None
        self.returncode_actual=None
        self.time_interval=None
        self.time_total=None
        self.files={}
        self.dirs={}
        self.stdout=None
        self.stderr=None
        self.stdverbose=None
        self.trace=None
        self.full_stream=None

    def TestTime(self):
        if self.testrun.time.interval is not None and self.time_interval != False:
            self.time_interval=True
        if self.testrun.time.total is not None and self.time_total != False:
            self.time_total=True
            
    def TestTotalTimeFailed(self):
        self.time_total=False
        
    def TestIntervalTimeFailed(self):
        self.time_interval=False
        
    def TestReturnCode(self,val):
        if self.testrun.returncode is not None:
            self.returncode=(val==self.testrun.returncode)
            self.returncode_actual=val
            
    def TestStdout(self):
        self.stdout=self.testrun.streams.TestStdout(os.path.join(self.test.location,"_tmp_%s_%s"%(self.test.name,self.testrun.name)))
    
    def TestStderr(self):
        self.stderr=self.testrun.streams.TestStderr(os.path.join(self.test.location,"_tmp_%s_%s"%(self.test.name,self.testrun.name)))
        
    def TestStdVerbose(self):
        self.stdverbose=self.testrun.streams.TestStdVerbose(os.path.join(self.test.location,"_tmp_%s_%s"%(self.test.name,self.testrun.name)))
    
    def TestStdTrace(self):
        self.stdtrace=self.testrun.streams.TestStdTrace(os.path.join(self.test.location,"_tmp_%s_%s"%(self.test.name,self.testrun.name)))
        
    def TestFullStream(self):
        self.full_stream=self.testrun.streams.TestFullStream(os.path.join(self.test.location,"_tmp_%s_%s"%(self.test.name,self.testrun.name)))
        
    def TestFiles(self):
        for file in self.testrun.disk.files:
            tmp={}
            if os.path.isfile(file.name):
                tmp['exists']=True
            else:
                tmp['exists']=False
            tmp['size'],tmp['size_actual']=file.TestSize()
            tmp['content']=file.TestContent()
            self.files[file.name]=tmp
    
    def TestDirs(self):
        for dir in self.testrun.disk.dirs:
            tmp={}
            if os.path.isdir(dir.name):
                tmp['exists']=True
            else:
                tmp['exists']=False
            self.dirs[dir.name]=tmp    
            
    def quick_sumary(self):
        
        ## figure out if we had any issues
        
        if self.time_interval==False:
            return "Failed - time interval"
        if self.time_total==False:
            return "Failed - time total"
        if self.returncode == False:
            return "Failed - return code"
        if self.stdout is not None and len(self.stdout) > 0:
            return "Failed - stdout mismatch"
        if self.stderr is not None and len(self.stderr) > 0:
            return "Failed - stderr mismatch"
        if self.stdverbose is not None and len(self.stdverbose) > 0:
            return "Failed - stdverbose mismatch"
        if self.stdtrace is not None and len(self.stdtrace) > 0:
            return "Failed - stdtrace mismatch"
        if self.full_stream is not None and len(self.full_stream) > 0:
            return "Failed - fullstream mismatch"
        for k,v in self.files.items():
            if v['exists']==False or v['size']==False or (v['content']is not None and len(v['content']) > 0):
                return "Failed - File test:",k
        
        for k,v in self.dirs.items():
            if v['exists']==False:
                return "Failed - Dir does not exists:",k
        
        return None

class TimeTotalError(Exception):
    pass
class TimeIntervalError(Exception):
    pass

class Engine(object):
    def __init__(self):
        self.mytests={}
        self.results={}
        

    def start(self):
        print "starting"
        # scan for tests
        self.scan_for_tests()
        # see if we have a select list of tests to run else run all of them
        
        if False: #replace with arg check
            pass
        else:
            for name,test in self.mytests.items():
                self.results[test.name]=self.run_test(test)
        
        #report out an issues
        self.makereport()
        
    def makereport(self):
        
        num_failures=0
        for rstlst in self.results.values():
          print_name=True
          for rst in rstlst:
            if rst.quick_sumary() is not None:
                # we have a error to report
                num_failures=num_failures+1
                if print_name:
                    print_name=False
                    print "Test %s had failures! Summary:"%(rst.test.name)
                print "    Test run %s:"%(rst.testrun.name)
                ## report if there was any timing issues
                # interval time
                print "\tTime Interval:",
                if rst.testrun.time.interval is None:
                    print "Not tested"
                elif rst.time_interval == True:
                    print "Passed"
                else:
                    print "Failed"
                #total time    
                print "\tTime Total:",
                if rst.testrun.time.total is None:
                    print "Not tested"
                elif rst.time_total == True:
                    print "Passed"
                else:
                    print "Failed"
                ## report if there was issue with return code
                print "\tReturn code:",
                if rst.testrun.returncode is None:
                    print "Not tested"
                elif rst.returncode == True:
                    print "Passed"
                else:
                    print "Failed! expected: %s actual: %s"%(rst.testrun.returncode,rst.returncode_actual)
                ## report any diff with the stream
                #stdout
                print "\tstdout stream:",
                if rst.testrun.streams.stdout is None:
                    print "Not tested"
                elif rst.stdout == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdout
                    print "**************"
                #stderr
                print "\tstderr stream:",
                if rst.testrun.streams.stderr is None:
                    print "Not tested"
                elif rst.stdout == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdout
                    print "**************"
                
                print "\tstdverbose stream:",
                if rst.testrun.streams.stdverbose is None:
                    print "Not tested"
                elif rst.stdverbose == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdverbose
                    print "**************"
                print "\tstdtrace stream:",
                if rst.testrun.streams.stdtrace is None:
                    print "Not tested"
                elif rst.stdtrace == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdtrace
                    print "**************"
                print "\tfull_stream stream:",
                if rst.testrun.streams.full_stream is None:
                    print "Not tested"
                elif rst.full_stream == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.full_stream
                    print "**************"
                
                # report any isses with files
                # report any isses with dirs
                
        if num_failures > 0:
            print "There were a total of",num_failures,"failures"
        else:
            print "Everything passed"
                
    
    def scan_for_tests(self):
        ret=[]
        for root, dirs, files in os.walk('.'):
            #print 'Searching for tests in:', root
            print "Looking for tests in",root
            if '.svn' in dirs:
                dirs.remove('.svn')
            #for d in dirs:
            #    if d.startswith("_tmp_"):
            #        dirs.remove(d)
            for f in files:
                if f.endswith('.test.py'):
                    name=f[:-len('.test.py')]
                    if self.mytests.has_key(name):
                        print "WARNING! overiding test",name, "with test in", root
                    print "   Found test",name
                    self.mytests[name]=Test(name,root)
                    
                    

    def run_test(self,test):
        '''Runs the testruns of a given test'''

        #First we need to load a given test
        print "Loading Test", test.name,'in',test.location,
        
        ## load the test data. this mean exec the data
        #create the locals we want to pass
        locals={'test':test,'TestTemplate':TestTemplate}
        #get full path
        tmp=os.path.join(test.location,test.name+".test.py")
        execfile(tmp,{},locals)
        print "Done"
        print "Creating test run directory data"
        # create test directory ( test_root+test_location+test_name)
        test_dir=os.path.normpath(os.path.join(test_root,test.location,test.name))
        # copy and directory data
        
        if test.copy_directory == True:
        # if this bool True copy the directory tree that has the test in it
            shutil.copytree(test.location,test_dir)
        elif type(test.copy_directory) is types.StringType and os.path.exists(test.copy_directory):
            shutil.copytree(test.copy_directory,test_dir)
        else:
            os.makedirs(test_dir)
        #copy the scontruct file
        tmp=os.path.join(test_dir,"sconstruct")
        if test.sconstruct_file is None:
            if os.path.exists(os.path.join(test.location,"SConstruct_"+test.name)):
                shutil.copy2(os.path.join(test.location,"SConstruct_"+test.name),tmp)
            if os.path.exists(os.path.join(test.location,"Sconstruct_"+test.name)):
                shutil.copy2(os.path.join(test.location,"Sconstruct_"+test.name),tmp)
            if os.path.exists(os.path.join(test.location,"sconstruct_"+test.name)):
                shutil.copy2(os.path.join(test.location,"sconstruct_"+test.name),tmp)                
            elif os.path.exists(os.path.join(test.location,"SConstruct")):
                shutil.copy2(os.path.join(test.location,"SConstruct"),tmp)
            elif os.path.exists(os.path.join(test.location,"Sconstruct")):
                shutil.copy2(os.path.join(test.location,"Sconstruct"),tmp)
            elif os.path.exists(os.path.join(test.location,"sconstruct")):
                shutil.copy2(os.path.join(test.location,"sconstruct"),tmp)

        elif type(test.sconstruct_file) is types.StringType:
            if os.path.exists(test.sconstruct_file):
                shutil.copy2(test.sconstruct_file,tmp)
            if os.path.exists(os.path.join(test.location,test.sconstruct_file)):
                shutil.copy2(os.path.join(test.location,test.sconstruct_file),tmp)
            
            #We want to copy the test run data to a temp run directory
        ret=[]
        # run each sequence, or each until we get an Error
        for t in test.run:    
            ret.append(self.do_test_run(test,t,test_dir))
        return ret

        

    def do_test_run(self,test,testrun,test_dir):        
        testresult=TestResult(test,testrun)
        rcode=-1
        print "Test %s run %s "%(test.name,testrun.name),
        try:
            rcode =self.spawn_command(test,testrun,test_dir)
        ## get any time based tests that failed
            # this means the process was killed
        except TimeIntervalError:
            testresult.TestIntervalTimeFailed()
        except TimeTotalError:
            testresult.TestTotalTimeFailed()
        testresult.TestTime()
            
        #    pass
        print".",
        
        ## test return code
        testresult.TestReturnCode(rcode)
        print"." ,       
        ## test if any file existance,size content tests
        testresult.TestFiles()
        print".",
        ## test and directory existance tests
        testresult.TestDirs()
        print".",
        ## test any streams tests
        testresult.TestStdout()
        testresult.TestStderr()
        testresult.TestStdVerbose()
        testresult.TestStdTrace()
        testresult.TestFullStream()
        
        tmp=testresult.quick_sumary()
        if tmp is None:
            print "Passed!"
        else:
            print " ",tmp
        return testresult


            
    def spawn_command(self,test,test_run,test_dir):
        # do the call
        output=stream_writter(os.path.join(test_dir,"_tmp_%s_%s"%(test.name,test_run.name)))
        command_line="cd %s && %s"%(test_dir,test_run.cmd)
        print command_line
        proc = subprocess.Popen(
            command_line,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        
        # get the output and redirect to files
        p1 = pipeRedirector(proc.stdout, output.WriteOut)
        p2 = pipeRedirector(proc.stderr, output.WriteErr)

        running = True
        start_time=time.time()
        while running:
            curr_time=time.time()
            # test time interval
            if test_run.time.interval is not None:
                if not p1.ok(test_run.time.interval,curr_time) or not p1.ok(test_run.time.interval,curr_time):
                    # we have an error
                    raise TimeIntervalError()
            # test total time
            if test_run.time.total is not None:
                
                if test_run.time.total < (curr_time - start_time):
                    # we have an error
                    raise TimeTotalError()
            #time.sleep(1)
            running=proc.poll() is None
            
            

        p1.close()
        p2.close()
        print "return code",proc.returncode
        return proc.returncode

class pipeRedirector:
    def _readerthread(self):
        l = ' '
        while l != '':
            l = self.pipein.readline()
            self.time=time.time()
                
            if l != "":
                self.writer(l)

    def __init__(self,pipein,writer):
        self.pipein = pipein
        self.writer = writer
        self.thread = threading.Thread(target=self._readerthread,
                args=())
        self.executing = True
        self.thread.start()
        self.time=None
        
        
    def ok(self,intval_time,curr_time):
        if self.time is None:
            return True
        return intval_time > curr_time-self.time

    def close(self):
        self.executing = False
        self.thread.join()
        self.pipein = None
        self.thread = None
        self.writer = None

warning_tests = [
    re.compile('((\s|\W)warnings?(\W\s|\s))|(warnings?\s?:)',re.IGNORECASE)
    ]

error_tests =[
    re.compile('((\s|\W)errors?(\W\s|\s))|(errors?\s?:)',re.IGNORECASE)
    ]

class stream_writter(object):

    stdout=0
    stderr=1
    
    def __init__(self,path):
        if os.path.exists(path)== False:
            os.makedirs(path)
        self.both=file(os.path.join(path,full_stream_file),'wb')
        self.errfile=file(os.path.join(path,err_stream_file),'wb')
        self.outfile=file(os.path.join(path,out_stream_file),'wb')
        self.verbose=file(os.path.join(path,verbose_stream_file),'wb')
        self.trace=file(os.path.join(path,trace_stream_file),'wb')

        self.cache= []

    def smart_match(self,str):        
        if re.match("Parts: Verbose: \[\w*\]",str) is not None:
            self.verbose.write(str)
        elif re.match("Trace: \[\w*\]",str) is not None:
            self.trace.write(str)
        

    def WriteOut(self,str):
        
        if self.cache==[]:
            self.cache.append( [stream_writter.stdout,str] )
        elif self.cache[-1][0] ==  stream_writter.stdout:
            self.cache[-1][1] += str
        else:
            self.cache.append( [stream_writter.stdout,str] )
        

    def WriteErr(self,str):
        if self.cache==[]:
            self.cache.append( [stream_writter.stderr,str] )
        elif self.cache[-1][0] ==  stream_writter.stderr:
            self.cache[-1][1] += str
        else:
            self.cache.append( [stream_writter.stderr,str] )
    
    def __del__(self):
        self._empty_cache()    

    def _empty_cache(self):
        
        for text in self.cache:
            
            if text[0] == stream_writter.stdout:
                brkup=text[1].split('\n')
                grpstr=''
                for s in brkup:
                    if s == '':
                        pass
                    elif grpstr == '':
                        grpstr=s+'\n'
                    elif s[0]==' ' or s[0]=='\t': # group indented text
                        grpstr+=s+'\n'
                    else:
                        self.both.write(grpstr)
                        self.outfile.write(grpstr)
                        self.smart_match(grpstr)
                        grpstr=s+'\n'
                else:
                    self.both.write(grpstr)
                    self.outfile.write(grpstr)
                    self.smart_match(grpstr)
            elif text[0] == stream_writter.stderr:
                brkup=text[1].split('\n')
                grpstr=''
                    
                for s in brkup:
                    if s == '':
                        pass
                    elif grpstr == '':
                        grpstr=s+'\n'
                    elif s[0]==' ' or s[0]=='\t': # group indented text
                        grpstr+=s+'\n'
                    else:
                        self.both.write(grpstr)
                        self.errfile.write(grpstr)
                        self.smart_match(grpstr)
                        grpstr=s+'\n'
                else:
                    self.both.write(grpstr)
                    self.errfile.write(grpstr)
                    self.smart_match(grpstr)
            else:
                # we have some error or unknown code
                pass
            

if __name__ == '__main__':
    engine=Engine()
    engine.start()
    #if os.path.exists(test_root):
    #    shutil.rmtree(test_root)

