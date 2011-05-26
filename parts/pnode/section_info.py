
import stored_info

class section_info(stored_info.stored_info):
    """description of class"""
    def __init__(self):
        self.name=''
        self.part=None
        self.exports={}
        self.esigs={}
        self.dependson=[]
        self.exported_requirements=set()
        self.force_load=False
        #self.build_context=[]
        #self.config_context=[]
        
    def GetConfigContext(self):
        '''This will get the config context for a given section
        and merge with the parts version as needed'''
        
        # currently we just use the Parts version
        return self.part.Stored.config_context
    
    def GetBuilderContext(self):
        '''This will get the builder context for a given section
        and merge with the parts version as needed'''
        
        # currently we just use the Parts version
        return self.part.Stored.build_context    

