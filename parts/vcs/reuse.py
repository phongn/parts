from .. import common
from .. import parts
from .. import reporter
from base import base
    
class reuse_part_vcs(base):
    """This object allow users to reuse the checkout location of another Part
    
    In Parts this will be seen as VcsReuse. The old name of VcsUsePriorPart will be mapped this.
    This class is basically a proxy class.
    """

    def __init__(self,part):
        super(reuse_part_vcs,self).__init__("","")
        self._partref=part
                    
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
    def FullPath(self):
        ''' returns the full path'''
        return self._vcs.FullPath
    
    @property
    def CheckOutDir(self):
        '''Forward the vcs check out directory value
        ''' 
        return self._vcs.CheckOutDir
    
    #@property
    #def PartFileName(self):
    #    '''Forward the vcs file name value
    #    ''' 
    #    return self._vcs.PartFileName
    
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
        #when we setup this object we want
        # get the real vcs object so we can proxy it
        if  isinstance(self._partref,parts.Part_t):
            self._vcs=self._partref.Vcs
        elif common.is_string(self._partref):
            # assume this is a part alias
            self._vcs=common.g_engine._part_manager._from_alias(self._partref).Vcs
        else:
            reporter.report_error('VcsReuse was unable to map the vcs object to part "%s"'%(self._partref))
        self._env['VCS']=self._vcs._env['VCS'].clone()
        
    def NeedsToUpdate(self):
        '''Forward the vcs need to update value
        ''' 
        return self._vcs.NeedsToUpdate()
    
    def do_update_check(self):
        '''Function that should be used by subclass to add to any custom update logic that should be checked'''
        
        return self._vcs.do_update_check
    
    def do_exist_logic(self):
        ''' call for testing if the vcs think the stuff exists
        
        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self._vcs.do_exist_logic
            
    def do_check_logic(self):
        ''' call for checking if what we have in the data cache is matching the current checkout request 
        in the SConstruct match up
        
        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self._vcs.do_check_logic
            
    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used
        
        returns None if it passes, returns a string to possible print tell why it failed
        '''
        return self._vcs.do_force_logic
    
    def UpdateOnDisk(self):
        '''Forward the vcs update logic
        ''' 
        return self._vcs.UpdateOnDisk()
            

    def clean_step(self,out_dir):
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
    
    def ProcessResult(self,result):
        ''' this function returns the result of the given action call.
        
        @param result True or False based on if the Update logic was able to finish a successfull update
        
        Allow the a vcs upbject to setup an last minute state that it wants to. or store any data that might be needed
        for the next run
        '''
        return self._vcs.ProcessResult(result)
    
    def PostProcess(self):
        ''' This function is called when the system is done updating the disk
        This allows the object to update an data it needs on disk, or in the environment
        '''
        self._vcs.PostProcess()
        self._env['VCS']=self._vcs._env['VCS'].clone()
    
    
    
    
    
common.add_global_value('VcsReuse',reuse_part_vcs)
common.add_global_value('VcsUsePriorPart',reuse_part_vcs)
    
    