from .. import reporter 
                    
class task(object):
    ''' 
    This is a simple class that does nothing more than have the Vcs object update
    itself on disk. This is used to for parallel checkouts/updates.
    Someday SCons will formalize this code, that day we will have something to subclass form.
    Till then this is very dependent on SCons.. the names of the function have to be called this
    '''
    def __init__(self,vcs):
        self.__vcs = vcs
        self.__failed=False
    
    @property
    def Vcs(self):
        ''' Allow access to the VCS object as this is a VCS task'''
        return self.__vcs
        
    def prepare(self):
        ''' this is called before the task starts.
        
        Set up any logic or to figure out if anything should execute.
        '''
        pass
        
    def needs_execute(self):
        ''' reports if anything should execute'''
        return 1
    
    def execute(self):
        ''' this is what we call to do the checkout'''
        try:
            self.__vcs.UpdateOnDisk()
        #except PartRuntimeError:
            #pass
        except:
            
            import traceback,StringIO
            #ec_str=StringIO.StringIO()
            traceback.print_exc()#file=ec_str)
            raise
        
    def exception_set(self,exception=None):
        self.__failed=True
        
    def failed(self):
        if self.__failed:
            reporter.report_error("Vcs task failed for Part %s"%self.__vcs._env.get('ALIAS'),show_stack=False)
        
    def executed(self):
        ''' this gets called when everything execute() correctly'''
        pass

    def postprocess(self):
        ''' this always gets called after the task ran, failed or not'''
        self.__vcs.ProcessResult(not self.__failed)
        pass
        
