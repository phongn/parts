import sys
import linecache
import common
import console
import re
import os
import logger
import traceback
import string
import SCons.Script
# not ideal...
import SCons.Script.Main
import SCons.Errors

class PartRuntimeError(SCons.Errors.UserError):
    pass

g_rpter=None
class streamer:
    def __init__(self,outfunc):
        self.outfunc=outfunc
    def write(self,str):
        self.outfunc(msg=str)
    def flush(self):
        pass

warning_tests = [
    re.compile('((\s|\W)warnings?(\W\s|\s))|(warnings?\s?:)',re.IGNORECASE)
    ]

error_tests =[
    re.compile('((\s|\W)errors?(\W\s|\s))|(errors?\s?:)',re.IGNORECASE)
    ]

message_tests =[
    re.compile('(scons?\s?:)',re.IGNORECASE),
    re.compile('(parts?\s?:)',re.IGNORECASE),
    re.compile('(Install file?\s?:)'),
    ]

DEFAULT_STREAM=0
OUT_STREAM=1
MESSAGE_STREAM=2
WARNING_STREAM=3
ERROR_STREAM=4


def remap(s,org_stream):
    global last_type
    if s !="":
        if is_warning(s):
            return WARNING_STREAM
        if is_error(s):
            return ERROR_STREAM
        if is_message(s) and org_stream==OUT_STREAM:
            return MESSAGE_STREAM
    return DEFAULT_STREAM

def is_warning(str):
    for test in warning_tests:
        if test.search(str):
            return True
    return False

def is_error(str):
    for test in error_tests:
        if test.search(str):
            return True
    return False

def is_message(str):
    for test in message_tests:
        if test.search(str):
            return True
    return False

    
class reporter:
    def __init__(self,logger,silent,verbose):

        # so we can process any text that is being outputted by some other means
        sys.stdout=streamer(self.stdout)
        sys.stderr=streamer(self.stderr)        
        
        tmp=SCons.Script.GetOption('use_color')
        
        if tmp is not None and tmp.has_key('defaults') and \
            (os.isatty(sys.__stdout__.fileno()) ==False or os.isatty(sys.__stderr__.fileno()) ==False):
                tmp=None
        
        self.console=console.Console(tmp)
        self.logger=logger
        self.already_printed = set()
        self.silent=silent
        self.verbose=verbose
    
    def ShutDown(self):
        self.logger.ShutDown()
        self.console.ShutDown()
        

    def reset_logger(self,obj):
        ''' 
        reset the log data when our logger is a QueueLogger to the new 
        logger object by adding data in QueueLogger to new object
        '''
        if type(self.logger) is logger.QueueLogger:
            for t, msg in self.logger.queue:
                if t == console.Console.out_stream:
                    obj.logout(msg)
                elif t==console.Console.error_stream:
                    obj.logerr(msg)
                elif t==console.Console.warning_stream:
                    obj.logwrn(msg)
                elif t==console.Console.message_stream:
                    obj.logmsg(msg)
                elif t==console.Console.trace_stream:
                    obj.logtrace(msg)
                elif t==console.Console.verbose_stream:
                    obj.logverbose(msg)
            self.logger=obj
        
        
    def part_warning(self,msg,print_once=False,stackframe=None,show_stack=True):
        
        s="Parts: Warning: "+msg        
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content=stackframe
            else:
                filename, lineno, routine, content = GetPartStackFrameInfo()
            s+=' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine,content)
        
        if print_once ==True:
            if hash(s) not in self.already_printed:
                self.already_printed.add(hash(s))
            else:
                return
        self.console.Warning.write(s)
        self.logger.logwrn(s)
        
    def part_error(self,msg,stackframe=None,show_stack=True,exit=True):

        s="Parts: Error!: "+msg
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content=stackframe
            else:
                filename, lineno, routine, content = GetPartStackFrameInfo()
            s+=' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine,content)
        
        self.console.Error.write(s)
        self.logger.logerr(s)
        if exit:
            raise PartRuntimeError("Unrecoverable Error!")
        
    def part_message(self,msg):
        if self.silent ==False:
            s="Parts: "+msg
            self.stdmsg(s,False)

    def verbose_msg(self,catagory,msg):
        tmp=common.make_list(catagory)
        for c in tmp:
            if c in self.verbose:
                s='Parts: Verbose: ['+tmp[0]+"] "+msg
                self.stdverbose(s)
                break

    def trace_msg(self,catagory,msg):
        if self.trace:
            s='Trace: '+catagory+msg    
            self.stdtrace(s)
            
    def user_warning(self,env,msg,print_once=False,stackframe=None,show_stack=True):
        if env.get("PART_NAME") is None:
            s="User Warning: "+msg
        else:
            s='User Warning from Part Named "%s": %s'%(env.PartName(),msg)
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content=stackframe
            else:
                filename, lineno, routine, content = GetPartStackFrameInfo()
            s+=' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine,content)
        
        if print_once ==True:
            if hash(s) not in self.already_printed:
                self.already_printed.add(hash(s))
            else:
                return
        self.console.Warning.write(s)
        self.logger.logwrn(s)
        
    def user_error(self,env,msg,stackframe=None,show_stack=True,exit=True):

        if env.get("PART_NAME") is None:
            s="User Error: "+msg
        else:
            s='User Error from Part Named "%s": %s'%(env.PartName(),msg)
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content=stackframe
            else:
                filename, lineno, routine, content = GetPartStackFrameInfo()
            s+=' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine,content)
        
        self.console.Error.write(s)
        self.logger.logerr(s)
        if exit:
            raise PartRuntimeError("Unrecoverable Error!")
        
    def user_message(self,env,msg):
        if self.silent ==False:
            if env.get("PART_NAME") is None:
                s="Message: "+msg
            else:
                s='Message from Part "%s": %s'%(env.PartName(),msg)
            self.stdmsg(s,False)
            
            
    def remapped(self,msg,org_stream):
        remap_type = remap(msg,org_stream)
        if remap_type==DEFAULT_STREAM:
            return False        
        if remap_type == ERROR_STREAM:
            self.stderr(msg,False)
        elif remap_type == WARNING_STREAM:
            self.stdwrn(msg,False)
        elif remap_type == MESSAGE_STREAM:
            self.stdmsg(msg,False)

        return True
        
    def stdout(self,msg,remap=True):
        '''This function gets all redirected stdout text from random print calls'''
        if remap==True:
            if self.remapped(msg,OUT_STREAM)==False:
                self.console.Output.write(msg)
                self.logger.logout(msg)
        else:
            self.console.write(msg)
            self.logger.logout(msg)
         
    def stderr(self,msg,remap=True):
        '''This will gets any stderr text in scons via a print>>stderr usage'''
        #print>> sys.__stderr__, "Error message"
        if remap==True:
            if self.remapped(msg,ERROR_STREAM)==False:
                self.console.Error.write(msg)
                self.logger.logerr(msg)
        else:
            self.console.Error.write(msg)   
            self.logger.logerr(msg)
        
            
    def stdwrn(self,msg,remap=True):
        '''Unlike stdout and stderr, stdwrn doesn't really exist.. but we use
        this to pass text that is in a warning state from with in parts'''
        if remap==True:
            if self.remapped(msg,WARNING_STREAM)==False:
                self.console.Warning.write(msg)
                self.logger.logwrn(msg)
        else:
            self.console.Warning.write(msg)
            self.logger.logwrn(msg)
            
    def stdmsg(self,msg,remap=True):
        '''Unlike stdout and stderr, stdmsg doesn't really exist.. but we use
        this to pass text that is a message form the system parts or SCons'''
        if remap==True:
            if self.remapped(msg,MESSAGE_STREAM)==False:
                self.console.Message.write(msg)
                self.logger.logmsg(msg)
        else:
            self.console.Message.write(msg)
            self.logger.logmsg(msg)

    def stdtrace(self,msg,remap=True):
        '''Unlike stdout and stderr, stdtrace doesn't really exist.. '''
        self.console.Warning.write(msg)
        self.logger.logtrace(msg)

    def stdverbose(self,msg,remap=True):
        '''Unlike stdout and stderr, stdverbose doesn't really exist.. '''
        self.console.Verbose.write(msg)
        self.logger.logverbose(msg)
        

# no need to redirect data.. assume it is correct.
def report_error(*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    g_rpter.part_error(msg,kw.get('stackframe',None),kw.get('show_stack',True),kw.get('exit',True))

def report_warning(*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    g_rpter.part_warning(msg,kw.get('print_once',False),kw.get('stackframe',None),kw.get('show_stack',True))
    
def print_msg(*lst,**kw):
    msg=map(str,lst)
    g_rpter.part_message(kw.get('sep',' ').join(msg)+kw.get('end','\n'))

def verbose_msg(catagory,*lst,**kw):
    catagory=common.make_list(catagory)
    catagory.append('all')
    if g_rpter is not None:
        msg=map(str,lst)
        g_rpter.verbose_msg(catagory,kw.get('sep',' ').join(msg)+kw.get('end','\n'))
    else:
        tmp=catagory
        ver=SCons.Script.GetOption('verbose')
        for c in tmp:
            if c in ver:
                msg=map(str,lst)
                sys.stdout.write('Parts: Verbose: ['+tmp[0]+"] "+kw.get('sep',' ').join(msg)+kw.get('end','\n'))
                break        
        
def trace_msg(*lst,**kw):
    msg=map(str,lst)
    g_rpter.stdtrace(kw.get('sep',' ').join(msg)+kw.get('end','\n'))

## user level functions
# global version (for Sconstruct file)
def user_report_error(*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    g_rpter.user_error(SCons.Script.DefaultEnvironment(),msg,kw.get('stackframe',None),kw.get('show_stack',False))

def user_report_warning(*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    g_rpter.user_warning(SCons.Script.DefaultEnvironment(),msg,kw.get('print_once',False),kw.get('stackframe',None),kw.get('show_stack',False))
    
def user_print_msg(*lst,**kw):
    msg=map(str,lst)
    g_rpter.user_message(SCons.Script.DefaultEnvironment(),kw.get('sep',' ').join(msg)+kw.get('end','\n'))
    
def user_verbose(catagory,*lst,**kw):
    catagory=common.make_list(catagory)
    catagory.append('user')
    msg=map(str,lst)
    g_rpter.verbose_msg(catagory,kw.get('sep',' ').join(msg)+kw.get('end','\n'))
    
# env version
def user_report_error_env(env,*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    g_rpter.user_error(env,msg,kw.get('stackframe',None),kw.get('show_stack',True))

def user_report_warning_env(env,*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    g_rpter.user_warning(env,msg,kw.get('print_once',False),kw.get('stackframe',None),kw.get('show_stack',False))
    
def user_print_msg_env(env,*lst,**kw):
    msg=map(str,lst)
    g_rpter.user_message(env,kw.get('sep',' ').join(msg)+kw.get('end','\n'))
    
def user_verbose_env(env,catagory,*lst,**kw):
    catagory=common.make_list(catagory)
    catagory.append('user')
    msg=map(str,lst)
    g_rpter.verbose_msg(catagory,kw.get('sep',' ').join(msg)+kw.get('end','\n'))


# stuff to help with reporting debug info
def ResetPartStackFrameInfo():
    if len(common.g_part_frame) > 0:
        common.g_part_frame.pop(0)

def list_endwith(str, lst):
        str=str.lower()
        for l in lst:
            l=l.lower()
            if str.endswith(l):
                return True
        return False

def SetPartStackFrameInfo(use_existing=False):
    # putting tuple of (filename, line, routine, content) into common.g_part_frame
    if use_existing==True:
        if len(common.g_part_frame) > 0:
            common.g_part_frame.insert(0,common.g_part_frame[0])
            return 

    # We avoid using of inspect.* functions here because
    # the functions are redundant in this case and add
    # additional overhead.
            
    # The following returns a frame of SetPartStackFrameInfo caller
    # we will use its values as default return data
    frame = sys._getframe(1)
    part_frame = frame
    try:
        checked = False
        while part_frame:
            if not checked:
                # determining best parts source to return
                if not part_frame.f_code.co_filename.endswith('parts'+os.sep+'reporter.py'):
                    frame = part_frame
                    checked = True
            if list_endwith(part_frame.f_code.co_filename, [".parts", ".part", "sconstruct"]):
                break
            part_frame = part_frame.f_back
        else:
            part_frame = frame

        assert(not part_frame is None)
        lineno = part_frame.f_lineno
        line = linecache.getline(part_frame.f_code.co_filename, lineno)
        common.g_part_frame.insert(0, (part_frame.f_code.co_filename,lineno,part_frame.f_code.co_name,line))

    finally:
        # We delete frame and part_frame here to avoid leaking refernce to frame
        # such leaks "can cause your program to create reference cycles. Once a 
        # reference cycle has been created, the lifespan of all objects which
        # can be accessed from the objects which form the cycle can become much
        # longer even if Python's optional cycle detector is enabled. If such
        # cycles must be created, it is important to ensure they are explicitly
        # broken to avoid the delayed destruction of objects and increased
        # memory consumption which occurs."

        del frame
        del part_frame
    

# some functions to get the current stack frame of interest for reporting purposes
def GetPartStackFrameInfo():
    
    if common.g_part_frame == []:
        SetPartStackFrameInfo()
        ret = common.g_part_frame[0]
        ResetPartStackFrameInfo()
    else:
        ret = common.g_part_frame[0]
    
    if ret is []:
        return ("unknown","unknown","unknown","unknown")
    #print "->",ret
    return ret
        
    
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

common.AddBoolVariable('STREAM_WARNING_AS_ERROR',False, 'Controls is warning based messages are treated as errors')

common.add_global_value('PrintError',user_report_error)
common.add_global_value('PrintWarning',user_report_warning)
common.add_global_value('PrintMessage',user_print_msg)
common.add_global_value('VerboseMessage',user_verbose)

# adding logic to Scons Enviroment object
SConsEnvironment.PrintError=user_report_error_env
SConsEnvironment.PrintWarning=user_report_warning_env
SConsEnvironment.PrintMessage=user_print_msg_env
SConsEnvironment.VerboseMessage=user_verbose_env
