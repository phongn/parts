
import os
from .. import common

    
class base(object):
    ''' 
    Base object for all VCS (version control systems) objects
    
    Contain the base logic for all the vcs type objects. All objects should use 
    this object as its base. The intent of this logic to support getting of sources
    for building not the checking of sources. Check in, push or other maintainance
    logic should be done outside SCons and Parts.
    '''
    
    
    def __init__(self,repository,server=None):
        '''Constructor for the vcs object
        @param self The object pointer
        @param repository The location under in the server to find get the data files
        @param server The vcs server to access. If not provided the full value of the repository value is used
        '''
        
        self._repository=repository
        self._server=server
        self._allow_parallel=True
        self._pobj=None
        self._env=None
        
    @property
    def Server(self):
        '''returns the value of the server
        
        Subclasses may add to this logic as they might want to define other values to fall back on if the
        server value if None. For example the SVN object will return the value of $SVN_SERVER if the 
        server is not set
        ''' 
        return self._server
    @property
    def Repository(self):
        '''returns the value of the server
        
        Subclasses may add to this logic as they might want to define other values based on custom logic.
        '''
        return self._repository
    @property
    def CheckOutDir(self):
        '''returns the path in which we want to checkout to'''
        return self._env.Dir(self._env.subst('$CHECK_OUT_DIR')).path
    @property
    def PartFileName(self):
        '''returns the modifed path of the Parts file based on the check out directory'''
        return self._env.Dir(self.CheckOutDir).File(self._pobj._file).abspath
    @property 
    def PartFileExists(self):
        return os.path.exists(self.PartFileName)    
    
            
    def AllowParallelAction(self):
        # change this latter to get value of 
        # some policy/variable value
        return True
        
    def _setup_(self,partobj):
        ''' This sets up the vcs object data for real use
        @param partobj The part object that we will want to reference for certain data items
        '''
        
        # the set the part object
        self._pobj=partobj
        self._env=partobj.Env
        
        # set up the server and repository data
        if self._server and self._server[-1]!='/':
            self._server+='/'
        if self._repository.startswith('/') or self._repository.startswith('\\'):
            self._repository=self._repository[1:]           
        self.UpdateEnv()
        
    def UpdateEnv(self):
        ''' 
        Update the with information about the current VCS object
        '''
        self._env['VCS']=common.namespace(
                TYPE='unknown',
                CHECKOUT_DIR=''
            ) 
        
    def NeedsToUpdate(self):
        '''Tell us if this Vcs object believe it need to be updated'''
        if self.PartFileExists:
            #this file exists. so we check to see if the user wants the sources updated
            
            # this checks with the values for CLI -- options
            ## @todo finish this line
            update=self._env.GetOption('update')
            if self._env.Alias in update or 'all' in update:
                return True
            elif self.doNeedsToUpdate():
                return True
            # this check the backwards compatible way.. to be removed
            ## @todo remove this case in 0.10+1.0 version
            elif self._pobj.Env['UPDATE_ALL']==True:
                return True
            return False
        
        return True
    
    def doNeedsToUpdate(self):
        '''Function that should be used by subclass to add to any update logic that should be checked'''
        # this logic is the backward compatiblity ... to be removed
        alias=self._env['PART_ALIAS']
        return self._env.get('UPDATE_'+alias.upper(),None) is not None
        # when we remove the above two lines...
        return False
    
    def UpdateOnDisk(self):
        ''' This function does the update logic on the disk'''
        if self.PartFileExists:
            ret=self.Update()
        else:
            ret=self.CheckOut()
        if ret:
            reporter.report_error("Failure detected during checkout sources")
            

    def _clean_step(self,out_dir):
        '''
        Function to allow for any special actions that are needed before we clean.
        @param self object pointer
        @param out_dir The root directory that we want to clean

        normally does nothing but some vcs tool make read-only directories with state 
        that we want to clean up. Given then the Python will error when trying to clean 
        these items. This allow the tool to reset the state to a writable state so the
        scons -c command can correctly clean the data
        '''
        pass

    
    def UpdateAction(self,out_dir):    
        '''
        this is what would be called for any updating of the location
        
        @param self object pointer
        @param out_dir The location we want to update
        
        The out_dir value is added to help with fancy vcs objects that might want need
        to make and test different action cases
        '''
        return None
        
    def CheckOutAction(self,out_dir):
        '''
        this is what would be called when we need to get a fresh checkout copy
        
        @param self object pointer
        @param out_dir The location we want to checkout to
        
        The out_dir value is added to help with fancy vcs objects that might want need
        to make and test different action cases
        '''
        return None

    def Update(self):
        ''' This does the check update logic for a given tool
        
        Ideally this does not get overidden as the and tool only needs to provide a command to run
        '''
        
        action=self.UpdateAction(self._env,self.CheckOutDir)
        return self._env.Execute(action)
        
        

    def CheckOut(self):
        ''' This does the check update logic for a given tool
        
        Ideally this does not get overidden as the and tool only needs to provide a command to run
        '''
        
        action=self.CheckOutAction(self._env,self.CheckOutDir)
        return self._env.Execute(action)
           


######################


    #def __call__(self,out_dir,env,name):
    #    if common.g_part_mode=='clean':
    #        self.clean_step(out_dir)
    #        ret = True
    #    elif os.path.exists(out_dir):
    #        ret = self.update_cmd(out_dir,env,name)
    #    else:
    #        ret = self.checkout_cmd(out_dir,env,name)
    #    return ret



# add configuartion varaible needed for part

common.AddBoolVariable('UPDATE_ALL',False,'Controls if Parts will update source from servers')
common.AddVariable('CHECK_OUT_ROOT','#vcs','Root directory to place checked out data')
common.AddVariable('CHECK_OUT_DIR','$VCS_DIR','Full path used for any given checked out item')
common.AddVariable('VCS_DIR','$VCS.CHECKOUT_DIR','')
common.AddVariable('VCS_PREBUILDS_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')