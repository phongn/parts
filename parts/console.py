import common
import sys

class StreamWrapper:
    def __init__(self,stream):
        self.stream=stream
        
    def Write(self,s):
        ## set color
        
        ## write data
        self.stream.write(s)
        ## reset color        
    
    def WriteLines(self,str_list):
        ## set color
        
        ## write data
        self.stream.writelines(str_list)
        ## reset color            
    
    def Color(self,val):
        pass
    
    def BackgroundColor(self,val):
        pass


class Console:
    ''' only support output operations at this time'''
    def __init__(self,warning_as_error_stream=False):
        self.Output=StreamWrapper(sys.__stdout__)
        self.Error=StreamWrapper(sys.__stderr__)
        if warning_as_error_stream==True:
            self.Warning=StreamWrapper(sys.__stderr__)
        else:
            self.Warning=StreamWrapper(sys.__stdout__)
    
    def Write(self,msg):
        ## write data
        self.Output.Write(msg)
    
    def WriteLines(self,msg_lst):
        ## write data
        self.Output.Write(msg_lst)
        
        
        