
import stored_info

class scons_node_info(stored_info.stored_info):
    """description of class"""
    def __init__(self):
        self.type=None
        self.issymlink=False
        self.components={}
        self.side_effects=[]
        # self.srcnode # optional value that exist only if needed
        
    def SrcNode(self,other):
        return getattr(self,'srcnode',other)
    
        
        
        