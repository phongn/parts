import common
import os

class nil_logger:
    
    def __init__(self,dir="",file=""):
        pass
    
    def log(self,msg):
        pass
        
    def logerr(self,msg):
        pass
        
    def logwrn(self,msg):
        pass
    
    def __del__(self):
        pass

class text_logger:
    
    def __init__(self,dir,file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        self.m_file=open(os.path.join(dir,file),"w")
    
    def log(self,msg):
        self.m_file.write(msg)
        
    def logerr(self,msg):
        self.m_file.write(msg)
        
    def logwrn(self,msg):
        self.m_file.write(msg)
    
    def __del__(self):
        if self.__dict__.has_key('m_file') == False:
            return 
        self.m_file.close()
        

common.AddVariable('LOGGER','NIL_LOGGER','')
common.AddVariable('NIL_LOGGER',nil_logger,'')
common.AddVariable('TEXT_LOGGER',text_logger,'')        
common.AddVariable('LOG_ROOT_DIR','#logs','')
common.AddVariable('LOG_DIR','${LOG_ROOT_DIR}','')
common.AddVariable('LOG_FILE_NAME','all.log','')        
        