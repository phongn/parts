

import parts.logger as logger
import os

class text(logger.Logger):
    
    def __init__(self,dir,file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        self.m_file=open(os.path.join(dir,file),"w")
        
    def logout(self,msg):
        self.m_file.write(msg)
        
    def logerr(self,msg):
        self.m_file.write(msg)
        
    def logwrn(self,msg):
        self.m_file.write(msg)
    
    def logmsg(self,msg):
        self.m_file.write(msg)

    def logtrace(self,msg):
        self.m_file.write(msg)
    
    def logverbose(self,msg):
        self.m_file.write(msg)
    
    def shutdown(self):
        if self.__dict__.has_key('m_file') == False:
            return 
        self.m_file.close()