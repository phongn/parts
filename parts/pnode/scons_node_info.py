from .. import glb
import stored_info

class scons_node_info(stored_info.stored_info):
    """description of class"""
    __slots__=[
        '__type',
        '__components',
        '__side_effect_IDs',
        '__always_build',
        '__srcnodeID',
        '__source_info'
    ]
    def __init__(self):
        self.__type=None
        self.__components={}
        self.__side_effect_IDs=[]
        self.__always_build=False
        #optional value that tells us the ID of the source node
        # may be None as there is no "variant" for this node.
        # This happen with the variant source node that does not
        # point to the real source, but the variant that might be copied
        # in the build variant directory
        self.__srcnodeID=None 
        # this is a limited version of the SCons Binfo
        self.__source_info=None
        
    @property
    def Type(self):
        return self.__type
    @Type.setter
    def Type(self,val):
        self.__type=val

    @property
    def Components(self):
        return self.__components
    @Components.setter
    def Components(self,val):
        self.__components=val

    @property
    def SideEffectIDs(self):
        return self.__side_effect_IDs
    @SideEffectIDs.setter
    def SideEffectIDs(self,val):
        self.__side_effect_IDs=val

    @property
    def AlwaysBuild(self):
        return self.__always_build
    @AlwaysBuild.setter
    def AlwaysBuild(self,val):
        self.__always_build=val

    @property
    def SrcNodeID(self):
        return self.__srcnodeID
    @SrcNodeID.setter
    def SrcNodeID(self,val):
        self.__srcnodeID=val
    
    @property
    def SourceInfo(self):
        return self.__source_info
    
    @SourceInfo.setter
    def SourceInfo(self,val):
        self.__source_info=val
            
    def SrcNode(self,other):
        if self.__srcnodeID:
            return glb.pnodes.GetNode(self.__srcnodeID)
        return other
    
    
    
        
        