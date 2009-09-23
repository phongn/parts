import common
import sys
import set_color
import pdb
import string
import traceback
import SCons.Script
import thread

class StreamWrapper:
    OUTPUT = 0
    ERROR = 1
    WARNING = 2
    SET = 1
    RESET = 0
    def __init__(self,name,stream):
        self.name = name
        self.stream=stream
        # put an if statement here for posix or win32
        self.set_color = set_color.colors()
        self.def_env=SCons.Script.DefaultEnvironment()
        self.COLOR_ON = self.def_env["use_color"]
        self.m_lock=thread.allocate_lock()
               
    def Color(self,action,msg):
        if action == StreamWrapper.SET:
            self.m_lock.acquire()
            if self.name == StreamWrapper.ERROR:
                msg = self.set_color.set_color(self.set_color.RED,msg)
            elif self.name == StreamWrapper.WARNING:
                msg = self.set_color.set_color(self.set_color.YELLOW,msg)
            else:
                msg = self.set_color.set_color(self.set_color.orig_color,msg)
        else:
            msg = self.set_color.set_color(self.set_color.orig_color,msg)
            self.m_lock.release()
        return msg
        
    def Write(self,s):
        ## set color
        if self.COLOR_ON:
            s = self.Color(StreamWrapper.SET,s)        
        ## write data
        self.stream.write(s)
        ## reset color
        if self.COLOR_ON:
            s = self.Color(StreamWrapper.RESET,s)

    
    def WriteLines(self,str_list):
        ## set color
        if self.COLOR_ON:
            s = self.Color(StreamWrapper.SET,s)        
        ## write data
        self.stream.writelines(str_list)
        ## reset color
        if self.COLOR_ON:
            s = self.Color(StreamWrapper.RESET,s)

      
    
    def BackgroundColor(self,val):
        pass


class Console:
    ''' only support output operations at this time'''
    def __init__(self,warning_as_error_stream=False):
        self.Output=StreamWrapper(StreamWrapper.OUTPUT,sys.__stdout__)
        self.Error=StreamWrapper(StreamWrapper.ERROR,sys.__stderr__)
        if warning_as_error_stream==True:
            self.Warning=StreamWrapper(StreamWrapper.WARNING,sys.__stderr__)
        else:
            self.Warning=StreamWrapper(StreamWrapper.WARNING,sys.__stdout__)
    
    def Write(self,msg):
        ## write data
        #print>> sys.__stderr__, "Console::Write()"
        self.Output.Write(msg)
    
    def WriteLines(self,msg_lst):
        ## write data
        self.Output.Write(msg_lst)
        
        
        