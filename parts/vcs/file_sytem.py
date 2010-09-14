from base import base
from .. import common
from .. import reporter
import SCons.Defaults
import os

class file_sytem(base):
    """Allows thr retrieval of items from a file based system
    
    Mapped as VcsFileSystem and VcsPreBuilds
    """

    @base.Server.getter
    def Server(self):
        ''' svn property override to getting server data'''
        if self._server is not None:
            return self._server
        try:
            return self._env['FILE_SYSTEM_SERVER']
        except KeyError:    
            try:
                tmp=self._env['PREBUILT_SERVER']
                reporter.report_warning("PREBUILT_SERVER is depracated. Please use FILE_SYSTEM_SERVER instead",show_stack=False)
            except:
                pass
        return ''
    
    @property
    def full_path(self):
        ''' returns the full path (server + repository)
        '''
        return os.path.normpath(os.path.join(self.Server,self.Repository))
    
    def UpdateAction(self,out_dir):
        ''' The file system update action
        
        Currently is implemented in term of SCons default Actions
        '''
        
        cmdlst=[
            SCons.Defaults.Delete(out_dir,False),
            SCons.Defaults.Copy(self.full_path,out_dir)
            ]
        return self._env.Action(cmdlst,"VcsFileSystem: Updating Files from %s to %s"%(self.full_path,out_dir))
    
    def CheckOutAction(self,out_dir):
        ''' The file system check out action
        
        Currently is implemented in term of SCons default Actions
        '''
        
        cmdlst=[
            SCons.Defaults.Delete(out_dir,False),
            SCons.Defaults.Copy(self.full_path,out_dir)
            ]
        return self._env.Action(cmdlst,"VcsFileSystem: Copying Files from %s to %s"%(self.full_path,out_dir))
    
    def UpdateEnv(self):
        ''' 
        Update the with information about the current VCS object
        '''
        env['VCS']=common.namespace(
                TYPE='file_system',
                CHECKOUT_DIR='$VCS_FILESYSTEM_DIR',
            )

common.AddVariable('VCS_FILESYSTEM_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')
common.AddVariable('VCS_PREBUILDS_DIR','${VCS_FILESYSTEM_DIR}') #compatibility

common.add_global_value('VcsFileSystem',file_sytem)
common.add_global_value('VcsPreBuilt',file_sytem) # compatiblity
