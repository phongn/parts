import common
import os
import console #for stream types

class Logger(object):
    def __init__(self,dir="",file=""):
        pass
    
    def logout(self,msg):
        pass
        
    def logerr(self,msg):
        pass
        
    def logwrn(self,msg):
        pass
                
    def logmsg(self,msg):
        pass

    def logtrace(self,msg):
        pass    
    
    def logverbose(self,msg):
        pass
    
    def ShutDown(self):
        self.shutdown()
    
    def shutdown(self):
        pass


class QueueLogger(Logger):
    def __init__(self,dir="",file=""):
        self.queue=[]
    
    def logout(self,msg):
        self.queue.append((console.Console.out_stream,msg))
        
    def logerr(self,msg):
        self.queue.append((console.Console.error_stream,msg))
        
    def logwrn(self,msg):
        self.queue.append((console.Console.warning_stream,msg))
        
    def logmsg(self,msg):
        self.queue.append((console.Console.message_stream,msg))

    def logtrace(self,msg):
        self.queue.append((console.Console.trace_stream,msg))
    
    def logverbose(self,msg):
        self.queue.append((console.Console.verbose_stream,msg))
    
    

class nil_logger(Logger):
    pass
    



common.AddVariable('LOGGER','NIL_LOGGER','')

common.AddVariable('TEXT_LOGGER','text','')        
common.AddVariable('LOG_ROOT_DIR','#logs','')
common.AddVariable('LOG_DIR','${LOG_ROOT_DIR}','')
common.AddVariable('LOG_FILE_NAME','all.log','')        
        