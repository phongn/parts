
from .. import common
from base import base

import os

class svn(base):
    ''' This is the implmentation of the vcs SVN logic'''
    
    svnpath=None #the path to the svn program to run
    
    def __init__(self,repository,server=None,revision=None):
        '''Constructor call for the SVN object
        @param repository The repository or path from server under the server to get our data from
        @param server The server to connect to
        @param revision The optional revision to get. Defaults to latest revision
        '''
        self.__revision = revision
        super(svn, self).__init__(repository,server)
    
    @base.Server.getter
    def Server(self):
        ''' svn property override to getting server data'''
        if self._server is not None:
            return self._server
        return self._env['SVN_SERVER']
    
    @property
    def full_path(self):
        ''' returns the full path (server + repository)'''
        return os.path.join(self.Server,self.Repository).replace('\\','/')
    
    @property
    def Revision(self):
        rev_string=''
        if self.__revision:
            rev_string = '@' + self.__revision + ' '
        else:
            try:
                rev_string = '@' + self._env['SVN_REVISION'] + ' '
            except KeyError:
                pass
            except TypeError:
                pass
        return rev_string
    
    def UpdateAction(self):
        '''Returns the update Action for SVN
        
         in reality we may want to say update this area with a different version; the switch
         command is the more correct option in this case than the update command!

         we get here because out_dir already exists and they asked us to do
         something (UPDATE_ALL or UPDATE_FROM_SVN), or because it exists, but
         the part_file is missing ... in all cases we act the same way
         '''
         
        strval = '%s switch --non-interactive %s%s "%s"'%('svn',self.full_path,self.Revision,out_dir)
        cmd = '"%s" switch --non-interactive %s%s "%s"'%(svn.svnpath,self.full_path,self.Revision,out_dir)
        return self._env.Action(cmd,strval)
        
    def CheckOutAction(self,out_dir):
        ''' returns the action to do the checkout'''
            
        strval = '%s checkout --non-interactive %s%s "%s"'%('svn',self.full_path,self.Revision,out_dir)
        cmd = '"%s" checkout --non-interactive %s%s "%s"'%(svn.svnpath,self.full_path,self.Revision,out_dir)
        return self._env.Action(cmd,strval)
        
    def clean_step(self,out_dir):
        ''' since svn tends to checkout the .svn meta data area as readonly
        it turns out that we can't clean the checked out code correctly as 
        python will not clean the files that are readonly. This makes it so
        all the data is writable so we can do the delete actions
        '''
        
        import stat
        # small Hack to turn off SVN read only access so we can delete
        # the mess via clean
        for root, dirs, files in os.walk(out_dir, topdown=False):
            for f in files:
                source=os.path.join(root, f)
                st = os.stat(source)
                os.chmod(source, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
            for f in dirs:
                source=os.path.join(root, f)
                st = os.stat(source)
                os.chmod(source, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    def doNeedsToUpdate(self):
        # this is all backward compatibility that will be removed
        opt1=self._env.get('UPDATE_FROM_SVN',False)
        opt2=self._env.get('UPDATE_'+self._env['PART_ALIAS'].upper(),False)
        return opt1==True or opt2==True
    
    def UpdateEnv(self):
        ''' 
        Update the with information about the current VCS object
        '''
        if svn.svnpath is None:
            svn.svnpath=self._env.WhereIs('svn')
            if svn.svnpath is None:
                svn.svnpath=self._env.WhereIs('svn',os.environ['PATH'])
                
        self._env['VCS']=common.namespace(
                TYPE='svn',
                CHECKOUT_DIR='$VCS_SVN_DIR',
                PATH=svn.svnpath
            )
            
            
# add configuartion varaible needed for part
common.AddVariable('SVN_SERVER','','Value of SVN server to use')
common.AddBoolVariable('UPDATE_FROM_SVN',False,'Controls is Part will only update from SVN servers')
#common.AddVariable('SVN_REVISION',None,'Value of SVN revision to checkout, None mean latest' )
common.AddVariable('VCS_SVN_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')


common.add_global_value('VcsSvn',svn)
