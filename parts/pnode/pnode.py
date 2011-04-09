
from .. import glb


class pnode(object):
    """description of class"""  

    def __init__(self,ID):
        pass
        
    @property
    def Stored(self):
        try:
            return self.__stored
        except AttributeError:
            self.__stored=self.LoadStoredInfo()
        return self.__stored
    
    
    def LoadStoredInfo(self):
        raise NotImplementedError
        
    def StoreStoredInfo(self):
        raise NotImplementedError
        
    def GenerateStoredInfo(self):
        raise NotImplementedError
        
    @property
    def ID(self):
        raise NotImplementedError
        
    @property
    def isVisited(self):
        return getattr(self,'_isVisited',False)

    @isVisited.setter
    def _set_isVisited(self,value):
        self._isVisited=value
    
    def __repr__(self):
        return "<{1} object at 0x{2:x} ID={3}>".format(self.__module__,self.__class__.__name__,id(self),self.ID)
        

def pnode_factory(klass,*lst,**kw):
    '''Default factory logic for Pnode types'''
    
    # from input figure out the ID to get the node
    # and if we need to setup the node with passed in data
    id,setup=klass._process_arg(*lst,**kw)
    if id and setup and glb.pnodes.isKnownPNode(id):
        # we have the not .. Get it
        ret= glb.pnodes.GetPNode(id)
        # setup the node
        ret._setup_(*lst,**kw)
    elif id and setup and not glb.pnodes.isKnownPNode(id):
        #We don't have this node yet
        #make it 
        ret= klass(*lst,**kw)
        # setup the node
        ret._setup_(*lst,**kw)
        # register it
        glb.pnodes.AddPNodeToKnown(ret)
    elif id and not setup and glb.pnodes.isKnownPNode(id):
        # we have the not .. Get it
        ret= glb.pnodes.GetPNode(id)
    elif id and not setup and not glb.pnodes.isKnownPNode(id):
        #We don't have this node yet
        #make it 
        ret= klass(*lst,**kw)
        # register it
        glb.pnodes.AddPNodeToKnown(ret)
    elif not id: 
        #can not generate the ID early
        # so we make a node and call setup
        # at this point we have and ID
        ret= klass(*lst,**kw)
        ret._setup_(gen_ID=True,*lst,**kw)
        id=ret.ID
        # see if this is a known ID
        if glb.pnodes.isKnownPNode(id):
            #This is known
            # get this node and return it
            ret=glb.pnodes.GetPNode(id)
            # if this known, and it is not setup
            if setup and not ret.isSetup:
                # recall __init__ on the object
                ret.__init__(*lst,**kw)
        else:
            # else return the node we have and register it
            glb.pnodes.AddPNodeToKnown(ret)
        
        if setup and not ret.isSetup:
            # setup the node
            ret._setup_(*lst,**kw)
        
    return ret

