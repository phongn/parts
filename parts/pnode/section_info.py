
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
        
        

