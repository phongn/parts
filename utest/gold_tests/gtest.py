import re
import os
import subprocess
import time
import threading
import difflib

parts_path=os.path.abspath(os.path.normpath('../../'))
os.environ['PYTHONPATH']=parts_path


full_stream_file='stream.both.txt'
out_stream_file='stream.out.txt'
err_stream_file='stream.err.txt'
verbose_stream_file='stream.verbose.txt'
trace_stream_file='stream.trace.txt'

class Test(object):
    def __init__(self,name,location):
        #traits
        self.name=name
        self.location=location
        self.run_serial=False

        #required setup
        self.cmd="" # this is the command we want to run
        
        # possible stuff we can test
        # all cases below None means skip
        self.returncode=None # can be a int
        # time
        self.time=Time()
        self.streams=Stream(self)
        self.disk=Disk(self)
        


class Time(object):
    def __init__(self):
        self.total=None
        self.interval=None

class Stream(object):
    def __init__(self,test):
        self.test=test
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
    def __init__(self,name,exists=None):
        self.name=name
        self.exists=exists

class Disk(object):
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
    def __init__(self,test):
        self.test=test
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
        if self.test.time.interval is not None and self.time_interval != False:
            self.time_interval=True
        if self.test.time.total is not None and self.time_total != False:
            self.time_total=True
            
    def TestTotalTimeFailed(self):
        self.time_total=False
        
    def TestIntervalTimeFailed(self):
        self.time_interval=False
        
    def TestReturnCode(self,val):
        if self.test.returncode is not None:
            self.returncode=(val==self.test.returncode)
            self.returncode_actual=val
            
    def TestStdout(self):
        self.stdout=self.test.streams.TestStdout(os.path.join(self.test.location,"_tmp_"+self.test.name))
    
    def TestStderr(self):
        self.stderr=self.test.streams.TestStderr(os.path.join(self.test.location,"_tmp_"+self.test.name))
        
    def TestStdVerbose(self):
        self.stdverbose=self.test.streams.TestStdVerbose(os.path.join(self.test.location,"_tmp_"+self.test.name))
    
    def TestStdTrace(self):
        self.stdtrace=self.test.streams.TestStdTrace(os.path.join(self.test.location,"_tmp_"+self.test.name))
        
    def TestFullStream(self):
        self.full_stream=self.test.streams.TestFullStream(os.path.join(self.test.location,"_tmp_"+self.test.name))
        
    def TestFiles(self):
        for file in self.test.disk.files:
            tmp={}
            if os.path.isfile(file.name):
                tmp['exists']=True
            else:
                tmp['exists']=False
            tmp['size'],tmp['size_actual']=file.TestSize()
            tmp['content']=file.TestContent()
            self.files[file.name]=tmp
    
    def TestDirs(self):
        for dir in self.test.disk.dirs:
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
        for rst in self.results.values():
            if rst.quick_sumary() is not None:
                # we have a error to report
                num_failures=num_failures+1
                print rst.test.name,"had failures! Summary:"
                ## report if there was any timing issues
                # interval time
                print "Time Interval:",
                if rst.test.time.interval is None:
                    print "Not tested"
                elif rst.time_interval == True:
                    print "Passed"
                else:
                    print "Failed"
                #total time    
                print "Time Total:",
                if rst.test.time.total is None:
                    print "Not tested"
                elif rst.time_total == True:
                    print "Passed"
                else:
                    print "Failed"
                ## report if there was issue with return code
                print "Return code:",
                if rst.test.returncode is None:
                    print "Not tested"
                elif rst.returncode == True:
                    print "Passed"
                else:
                    print "Failed! expected:%s actual%s"%(rst.test.returncode,rst.returncode_actual)
                ## report any diff with the stream
                #stdout
                print "stdout stream:",
                if rst.test.streams.stdout is None:
                    print "Not tested"
                elif rst.stdout == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdout
                    print "**************"
                #stderr
                print "stderr stream:",
                if rst.test.streams.stderr is None:
                    print "Not tested"
                elif rst.stdout == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdout
                    print "**************"
                
                print "stdverbose stream:",
                if rst.test.streams.stdverbose is None:
                    print "Not tested"
                elif rst.stdverbose == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdverbose
                    print "**************"
                print "stdtrace stream:",
                if rst.test.streams.stdtrace is None:
                    print "Not tested"
                elif rst.stdtrace == "":
                    print "Passed"
                else:
                    print "Failed"
                    print "**** diff ****"
                    print rst.stdtrace
                    print "**************"
                print "full_stream stream:",
                if rst.test.streams.full_stream is None:
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
            for d in dirs:
                if d.startswith("_tmp_"):
                    dirs.remove(d)
            for f in files:
                if f.endswith('.test.py'):
                    name=f[:-len('.test.py')]
                    if self.mytests.has_key(name):
                        print "WARNING! overiding test",name, "with test in", root
                    print "   Found test",name
                    self.mytests[name]=Test(name,root)
                    
                    

    def run_test(self,test):
        print "Running Test", test.name,'in',test.location,
        testresult=TestResult(test)
        ## load the test data. this mean exec the data
        #create the locals we want to pass
        locals={'test':test}
        #get full path
        tmp=os.path.join(test.location,test.name+".test.py")
        execfile(tmp,{},locals)
        #exec open(tmp,"rb").read() in globals(),locals
        print ".",
        rcode=-1
        try:
            rcode =self.spawn_command(test)
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


            
    def spawn_command(self,test):
        # do the call
        output=stream_writter(os.path.join(test.location,"_tmp_"+test.name))
        command_line="cd %s && %s"%(test.location,test.cmd)
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
            if test.time.interval is not None:
                if not p1.ok(test.time.interval,curr_time) or not p1.ok(test.time.interval,curr_time):
                    # we have an error
                    raise TimeIntervalError()
            # test total time
            if test.time.total is not None:
                
                if test.time.total < (curr_time - start_time):
                    # we have an error
                    raise TimeTotalError()
            #time.sleep(1)
            running=proc.poll() is None
            
            

        p1.close()
        p2.close()
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


