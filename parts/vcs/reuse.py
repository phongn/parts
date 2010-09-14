from .. import common
from .. import parts
from base import base
    
class reuse_part_vcs(base):
    """This object allow users to reuse the checkout location of another Part
    
    In Parts this will be seen as VcsReuse. The old name of VcsUsePriorPart will be mapped this.
    This class is basically a proxy class.
    """

    def __init__(self,part):
        super(null_t,self).__init__("","")
        self._partref=part
        
    def _setup_(self,partobj):
        
        #when we setup this object we want
        # get the real vcs object so we can proxy it
        if  isinstance(self._partref,parts.Part_t):
            self._vcs=self._partref.Vcs
        elif common.is_string(part):
            # assume this is a part alias
            self._vcs=common.g_engine._part_manager._from_alias(self.partref).Vcs
        self.UpdateEnv()
            
    @property
    def Server(self):
        '''Forward the vcs server value
        ''' 
        return self._vcs.Server
    
    @property
    def Repository(self):
        '''Forward the vcs server value
        ''' 
        return self._vcs.Repository
    
    @property
    def CheckOutDir(self):
        '''Forward the vcs check out directory value
        ''' 
        return self._vcs.CheckOutDir
    
    @property
    def PartFileName(self):
        '''Forward the vcs file name value
        ''' 
        return self._vcs.PartFileName
    
    @property 
    def PartFileExists(self):
        '''Forward the vcs file exists value
        ''' 
        return self._vcs.PartFileExists
    
            
    def AllowParallelAction(self):
        '''Forward the vcs parallel action value
        ''' 
        return self._vcs.AllowParallelAction
        
    def UpdateEnv(self):
        ''' 
        fixme
        '''
        self._vcs._env['VCS']=common.namespace(
                TYPE='unknown',
                CHECKOUT_DIR=''
            ) 
        
    def NeedsToUpdate(self):
        '''Forward the vcs need to update value
        ''' 
        return self._vcs.NeedsToUpdate()
    
    
    def UpdateOnDisk(self):
        '''Forward the vcs update logic
        ''' 
        return self._vcs.UpdateOnDisk()
            

    def _clean_step(self,out_dir):
        '''Forward the vcs clean logic
        ''' 
        return self._vcs._clean_step(out_dir)
    
    def UpdateAction(self,out_dir):    
        '''Forward the vcs update action value
        ''' 
        return self._vcs.UpdateAction()
        
    def CheckOutAction(self,out_dir):
        '''Forward the vcs check out action value
        ''' 
        return self._vcs.CheckOutAction()

    def Update(self):
        '''Forward the vcs update logic'''
        return self._vcs.Update()

    def CheckOut(self):
        '''Forward the vcs update logic'''
        return self._vcs.CheckOut()
    
    
    
    
    
    
common.add_global_value('reuse_part_vcs',VcsReuse)
common.add_global_value('reuse_part_vcs',VcsUsePriorPart)
    
    