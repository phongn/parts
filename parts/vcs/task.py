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
        pass
        
    def needs_execute(self):
        ''' this always need to execute'''
        return 1
    
    def execute(self):
        ''' this is what we call to do the checkout'''
        self.__vcs.UpdateOnDisk()
        
        
    def exception_set(self,exception=None):
        self.__failed=True
        
    def failed(self):
        if self.__failed:
            reporter.report_error("Vcs task failed for Part %s"%self.__vcs._env.get('ALIAS'))
        
    def executed(self):
        pass

    def postprocess(self):
        pass