import os

import events
import host
import testers.equal
import conditions


class DelayedEventMapper(object):
    '''
    This class provides the base interface for creating predefined event mappings for a
    defined concept
    '''
    __slots__=[
               '__addevent',
               ]
    def __init__(self):
        self.__addevent={}

    def _BindEvents(self):
        for k,v in self.__addevent.iteritems():      
            event,callback=v
            event+=callback

    def _RegisterEvent(self,key,event,callback):
        self.__addevent[key]=(event,callback)

    def _GetRegisterEvent(self,key,event,callback):
        try:
            return self.__addevent[k]
        except KeyError:
            return None

class BaseTestRunItem(object):
    
    def __init__(self,testrun):
        self.__testrun=testrun

    def _RegisterEvent(self,key,event,callback):
        self.__testrun._RegisterEvent(key,event,callback)

    @property
    def _TestRun(self):
        return self.__testrun

class Streams(BaseTestRunItem):
    def __init__(self,testrun):
        super(Streams, self).__init__(testrun)

    #std streams
    @property
    def stdout(self):
        return self._GetRegisterEvent("Streams.stdout")

    @stdout.setter
    def stdout(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("stdout")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.stdout',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="StdOutFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    @property
    def stderr(self):
        return self._GetRegisterEvent("Streams.stderr")

    @stderr.setter
    def stderr(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("stderr")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.stderr',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="StdErrFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    #filtered streams
    @property
    def All(self):
        return self._GetRegisterEvent("Streams.All")

    @All.setter
    def All(self,val):
        return
        if isinstance(val,testers.Tester):
            val.TestValue("All")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.all',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="AllFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    @property
    def Message(self):
        return self._GetRegisterEvent("Streams.Message")

    @Message.setter
    def Message(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("Message")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.Message',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="MessageFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    @property
    def Warning(self):
        return self._GetRegisterEvent("Streams.Warning")

    @Warning.setter
    def Warning(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("Warning")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.Warning',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="WarningFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    @property
    def Error(self):
        return self._GetRegisterEvent("Streams.Error")

    @Error.setter
    def Error(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("Error")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.Error',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="ErrorFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    @property
    def Debug(self):
        return self._GetRegisterEvent("Streams.Debug")

    @Debug.setter
    def Debug(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("Debug")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.Debug',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="DebugFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")

    @property
    def Verbose(self):
        return self._GetRegisterEvent("Streams.Verbose")

    @Verbose.setter
    def Verbose(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue("Verbose")
        elif isinstance(val,basestring):
            self._RegisterEvent('Streams.Verbose',
                                 self._TestRun.RunFinished,
                                 testers.GoldFile(
                                                  File(self._TestRun,val,runtime=False),
                                                  test_value="VerboseFile"
                                                  )
                                 )
        else:
            host.WriteError("Invalid type")


class File(BaseTestRunItem):
    '''
    Allows us to test for a file. We can test for size, existance and content
    '''
    def __init__(self, testrun, name, exists = None, size = None, content_tester = None,execute=False,runtime=True):
        super(File, self).__init__(testrun)
        self.__name = name
        self.__runtime=runtime
        if exists: self.Exists = exists
        if size: self.Size = size
        if content_tester: self.Content = content_tester
        if execute: self.Execute = execute

    def __str__(self):
        return self.Name

    def GetContent(self,eventinfo):
        return self.AbsPath,""
        
    @property
    def AbsPath(self):
        '''
        The absolute path of the file, runtime value
        '''
        if self.__runtime:
         return self.AbsRunTimePath
        return self.AbsTestPath

    @property
    def AbsRunTimePath(self):
        '''
        The absolute path of the file, based on Runtime sandbox location
        '''
        tmp=os.path.normpath(os.path.join(self._TestRun._Test.RunDirectory,self.Name))
        return tmp

    @property
    def AbsTestPath(self):
        '''
        The absolute path of the file, based on directory relative form the test file location
        '''
        tmp=os.path.normpath(os.path.join(self._TestRun._Test.TestDirectory,self.Name))
        return tmp

    @property
    def Name(self):
        return self.__name

    @Name.setter
    def Name(self,val):
        self.__name=val

    @property
    def Exists(self):
        return self._GetRegisterEvent("File.Exists")
        
    @Exists.setter
    def Exists(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue(self)
        elif val == True:
            self._RegisterEvent('File.Exists',self._TestRun.RunFinished,testers.FileExists(True,self))
        elif val == False:
            self._RegisterEvent('File.Exists',self._TestRun.RunFinished,testers.FileExists(False,self))
        else:
            host.WriteError("Invalid type")
    
    def GetSize(self):
        statinfo = os.stat(self.AbsPath)
        return statinfo.st_size


    @property
    def Size(self):
        return self._GetRegisterEvent("File.Size")

    @Size.setter
    def Size(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue(self)
        else:
            try:
                val = int(val)
            except:
                host.WriteError("Invalid type")
            self._RegisterEvent('File.Size',self._TestRun.RunFinished,testers.Equal(val,test_value=self.GetSize))
            
    
    @property
    def Content(self):
        return self._GetRegisterEvent("File.Content")

    @Content.setter
    def Content(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue=self
        elif isinstance(val,basestring):
            self._RegisterEvent('File.Content',self._TestRun.RunFinished,
                                testers.GoldFile(
                                                 File(self._TestRun,val,runtime=False),
                                                 test_value=self)
                                )
        else:
            host.WriteError("Invalid type")
    
    @property
    def Executes(self):
        return self._GetRegisterEvent("File.Execute")

    @Executes.setter
    def Executes(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue(self)
        elif val == True:
            self._RegisterEvent('File.Execute',self._TestRun.RunFinished,testers.RunFile(True,self))
        elif val == False:
            self._RegisterEvent('File.Execute',self._TestRun.RunFinished,testers.RunFile(False,self))
        else:
            host.WriteError("Invalid type")
        self._RegisterEvent('File.Execute',self._TestRun.RunFinished,testers.RunFile(val,self))

class Directory(BaseTestRunItem):
    '''
    Allows us to test for a file. We can test for existance
    '''
    def __init__(self, testrun, name, exists = True, runtime=True):
        super(Directory, self).__init__(testrun)
        self.__name = name
        self.__runtime=runtime
        if exists: self.Exists = exists

    def __str__(self):
        return self.Name

    def GetContent(self,eventinfo):
        return self.AbsPath,""
        
    @property
    def AbsPath(self):
        '''
        The absolute path of the file, runtime value
        '''
        if self.__runtime:
         return self.AbsRunTimePath
        return self.AbsTestPath

    @property
    def AbsRunTimePath(self):
        '''
        The absolute path of the file, based on Runtime sandbox location
        '''
        tmp=os.path.normpath(os.path.join(self._TestRun._Test.RunDirectory,self.Name))
        return tmp

    @property
    def AbsTestPath(self):
        '''
        The absolute path of the file, based on directory relative form the test file location
        '''
        tmp=os.path.normpath(os.path.join(self._TestRun._Test.TestDirectory,self.Name))
        return tmp

    @property
    def Name(self):
        return self.__name

    @Name.setter
    def Name(self,val):
        self.__name=val

    @property
    def Exists(self):
        return self._GetRegisterEvent("Directory.Exists")

    @Exists.setter
    def Exists(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue(self)
        elif val == True:
            self._RegisterEvent('Directory.Exists',self._TestRun.RunFinished,testers.DirectoryExists(True,self))
        elif val == False:
            self._RegisterEvent('Directory.Exists',self._TestRun.RunFinished,testers.DirectoryExists(False,self))
        else:
            host.WriteError("Invalid type")

    
class Disk(BaseTestRunItem):
    '''
    allows use to define what kind of disk based test we want to do
    '''
    def __init__(self,testrun):
        super(Disk, self).__init__(testrun)
        self.__files={}
        self.__dirs={}

    def File(self,name,exists=None,size=None,content=None,execute=None,id=None,runtime=True):
        tmp=File(self._TestRun,name,exists,size,content,execute,runtime)
        if self.__files.has_key(name):
            host.WriteWarning("Overriding file object {0}".format(name))
        self.__files[name]=tmp
        if id:
            self.__dict__[id]=tmp
        return tmp

    def Directory(self,name,exists=None,id=None,runtime=True):
        tmp=Directory(self._TestRun,name,exists,runtime)
        if self.__dirs.has_key(name):
            host.WriteWarning("Overriding directory object {0}".format(name))
        self.__dirs[name]=tmp
        if id:
            self.__dict__[id]=tmp
        return tmp

class TestRun(DelayedEventMapper):
    '''
    A test run allows us to test a certain command and see if certian actions happened as excepted
    Special cases of Test run may test it a test is up-to-date, or out-of -date
    '''
    __slots__=["__displaystr",
               "__name",
               "__test",
               "__cmd",
               "__result",
               "__run_time",
               "__disk",
               "__streams",
               "StartingRun",
               "RunStarted",
               "Running",
               "RunFinished",
               ]
    def __init__(self,test,name,displaystr=None):
        super(TestRun, self).__init__()
        #required setup
        self.__displaystr=displaystr # what we display for this string
        self.__name=name # the test name
        self.__test=test # test object

        # what to run
        self.__cmd="" # this is the command we want to run

        # information about the run
        self.__result=None # the return code
        self.__run_time=None # the time in seconds of the run
        
        # objects with more stuff we can test.
        self.__disk=Disk(self)
        self.__streams=Streams(self) 

        #events that happen during run
        # these get mapped to test objects
        self.StartingRun=events.Event()
        self.RunStarted=events.Event()
        self.Running=events.Event()
        self.RunFinished=events.Event()
        
        
   
    @property
    def _Test(self):
        return self.__test

    def _RegisterEvents(self):
        self.__addevent

    def get_testers(self):
        testers=[]
        testers+=list(self.StartingRun.Testers)
        testers+=list(self.RunStarted.Testers)
        testers+=list(self.Running.Testers)
        testers+=list(self.RunFinished.Testers)
        return testers

    @property
    def _Result(self):
        if self.__result is None:
            for i in self.get_testers():
                if self.__result < i.Result:
                    self.__result = i.Result
        #if we are have no result and have nothing to test
        # we say we passed
        if self.__result is None and len(self.get_testers()) == 0:
            self.__result=testers.ResultType.Passed
        return self.__result
    
    @_Result.setter
    def _Result(self,val):
        self.__result=val

    @property
    def Name(self):
        return self.__name

    @property
    def DisplayString(self):
        if self._displaystr:
            return self._displaystr
        return self.name

    @DisplayString.setter
    def DisplayString(self):
        if self.__displaystr:
            return self.__displaystr
        return self.Name

    @property
    def Command(self):
        return self.__cmd

    @Command.setter
    def Command(self,value):
        value=value.replace('/',os.sep)
        self.__cmd=value
    
    # stuff to test
    @property
    def ReturnCode(self):
        return self._GetRegisterEvent("TestRun.ReturnCode")

    @ReturnCode.setter
    def ReturnCode(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue('ReturnCode')
        else:
            try: 
                val = int(val)
                self._RegisterEvent('TestRun.ReturnCode',self.RunFinished,testers.Equal(val,test_value='ReturnCode'))
            except ValueError:
                host.WriteError("Invalid type")
        
    @property
    def Time(self):
        return self._GetRegisterEvent("TestRun.Time")

    @Time.setter
    def Time(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue('TotalTime')
        else:
            try: 
                val = int(val)
                self._RegisterEvent('TestRun.Time',self.RunFinished,testers.Equal(val,test_value='TotalTime'))
            except ValueError:
                host.WriteError("Invalid type")

    @property
    def TimeOut(self):
        return self._GetRegisterEvent("TestRun.TimeOut")

    @TimeOut.setter
    def TimeOut(self,val):
        if isinstance(val,testers.Tester):
            val.TestValue('TotalTime')
        else:
            try: 
                val = int(val)
                self._RegisterEvent('TestRun.TimeOut',self.Running,testers.LessThan(val,test_value='TotalTime',kill=True))
            except ValueError:
                host.WriteError("Invalid type")

    @property
    def Disk(self):
       return self.__disk

    @property
    def Streams(self):
       return self.__streams


