
from .. import common
from .. import datacache
from .. import api
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
        self._disk_data=None
        self.__completed=None
        if repository.endswith('/'):
            repository=repository[:-1]
        if server and server.endswith('/'):
            server=server[:-1]
        super(svn, self).__init__(repository,server)
    
    @base.Server.getter
    def Server(self):
        ''' svn property override to getting server data'''
        if self._server is not None:
            return self._server
        return self._env['SVN_SERVER']
       
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
    
    
    def UpdateAction(self,out_dir):
        '''Returns the update Action for SVN
        
         in reality we may want to say update this area with a different version; the switch
         command is the more correct option in this case than the update command!
         '''
        
        #if the server is different we need to relocate
        update_path=self.FullPath
        
        if self.get_svn_data()['root'] != self.Server:
            strval1 ='%s switch --relocate $SVN_FLAGS %s %s "%s"'%('svn',self.get_svn_data()['root'],self.Server,out_dir)
            strval2 ='%s switch $SVN_FLAGS %s%s "%s"'%('svn',update_path,self.Revision,out_dir)
            
            cmd1= '"%s" switch --relocate $SVN_FLAGS %s %s "%s"'%(svn.svnpath,self.get_svn_data()['root'],self.Server,out_dir)
            cmd2= '"%s" switch $SVN_FLAGS %s%s "%s"'%(svn.svnpath,update_path,self.Revision,out_dir)
            return [self._env.Action(cmd1,strval1),self._env.Action(cmd2,strval2)]
        else:
            strval = '%s switch $SVN_FLAGS %s%s "%s"'%('svn',update_path,self.Revision,out_dir)
            cmd = '"%s" switch $SVN_FLAGS %s%s "%s"'%(svn.svnpath,update_path,self.Revision,out_dir)
        return self._env.Action(cmd,strval)
        
    def CheckOutAction(self,out_dir):
        ''' returns the action to do the checkout'''
        strval = '%s checkout $SVN_FLAGS %s%s "%s"'%('svn',self.FullPath,self.Revision,out_dir)
        cmd = '"%s" checkout $SVN_FLAGS %s%s "%s"'%(svn.svnpath,self.FullPath,self.Revision,out_dir)
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

                
    def do_update_check(self):
        '''Function that should be used by subclass to add to any custom update logic that should be checked'''
        # this is all backward compatibility that will be removed
        if self._env.get('UPDATE_FROM_SVN',False):
            return True
        return False
    
    def do_exist_logic(self):
        ''' call for testing if the vcs think the stuff exists that should be build
        
        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update","vcs_svn"]," Doing existance check")
        if self.PartFileExists and os.path.exists(os.path.join(self.CheckOutDir,'.svn')):
            return None
        api.output.verbose_msg(["vcs_update","vcs_svn"]," Existance check failed")
        self.__completed=False
        return "%s needs to be updated on disk"%self._pobj.Alias
            
    def do_check_logic(self):
        ''' call for checking if what we have in the data cache is matching the current checkout request 
        in the SConstruct match up
        
        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update","vcs_svn"]," Using check vcs logic.")
        #test for existance
        tmp=self.do_exist_logic()
        if tmp:
            self.__completed=False
            return tmp
        #get data cache and see if our paths match
        cache=datacache.GetCache(name=self._env['ALIAS'],key='vcs')
        if cache:
            api.output.verbose_msg(["vcs_update","vcs_svn"]," Cached server: %s"%(cache['server']))
            api.output.verbose_msg(["vcs_update","vcs_svn"]," Requested Server: %s"%(self.FullPath))
            if cache['server']!=self.FullPath:
                api.output.verbose_msg(["vcs_update","vcs_svn"]," Cache version of server does not match.. verifing on disk..")
                # hard check to verify it is really bad
                data=self.get_svn_data()
                if data:
                    if data['server'] != self.FullPath:
                        api.output.verbose_msg(["vcs_update","vcs_svn"]," Disk version does not match")
                        self.__completed=False
                        return 'Server on disk is different than the one requested for Parts "%s\n On disk: %s\n requested: %s"'%(self._pobj.Alias,data['server'],self.FullPath)
                    else:
                        api.output.verbose_msg(["vcs_update","vcs_svn"]," Disk version matches")
                else:
                    self.__completed=False
                    api.output.verbose_msg(["vcs_update","vcs_svn"]," Could not query disk version for information!")
                    return 'Disk copy seems bad... updating'
        else:
            api.output.verbose_msg(["vcs_update","vcs_svn"]," Data Cache does not exist.. doing force logic")
            return self.do_force_logic()
        
        
            
    def do_force_logic(self):
        ''' call for testing if what is one disk matches what the SConstruct says should be used
        
        returns None if it passes, returns a string to possible print tell why it failed
        '''
        api.output.verbose_msg(["vcs_update","vcs_svn"]," Using force vcs logic.")
        #test for existance
        tmp=self.do_exist_logic()
        if tmp:
            self.__completed=False
            api.output.verbose_msg(["vcs_update","vcs_svn"]," Existance checked failed")
            return tmp
        data=self.get_svn_data()
        if data:
            if data['server'] != self.FullPath:
                self.__completed=False
                api.output.verbose_msg(["vcs_update","vcs_svn"]," Disk checked failed")
                return 'Server on disk is different than the one requested for Parts "%s\n On disk: %s\n requested: %s"'%(self._pobj.Alias,data['server'],self.FullPath)
            else:
                return None
        
        
    
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
                TOOL=svn.svnpath,
                REVISION=None,
                SERVER_PATH=self.FullPath,
                MODIFIED=None,
                FLAGS=self._env['SVN_FLAGS']
            )
    def ProcessResult(self,result):
        ''' Handle SVN logic we want need to handle
        
        @param result True or False based on if the Update logic was able to finish a successfull update
        
        '''
        #Setup and store vcs data cache logic
        self.__completed=result

        
        
    def PostProcess(self):
        ''' This function is called when the system is done updating the disk
        This allows the object to update any data it needs on disk, or in the environment
        '''
        if self.__completed is None:
            self.__completed=True
        
        tmp={
        '__version__':1.0,
        'type':'svn',
        'server':self.FullPath,
        'completed':self.__completed
        }
         
        datacache.StoreData(name=self._env['ALIAS'],data=tmp,key='vcs')
        
        self._env["VCS"].REVISION=common.DelayVariable(lambda : self.get_svn_data()['revision'])
        self._env["VCS"].MODIFIED=common.DelayVariable(lambda :self.get_svn_data()['modified'])
        self._env["VCS"].PARTIAL=common.DelayVariable(lambda :self.get_svn_data()['partial'])
        self._env["VCS"].SWITCHED=common.DelayVariable(lambda :self.get_svn_data()['switched'])
   
    def get_svn_data(self):
        # get current state
        if self._disk_data is None:
            server=None
            root=None
            modified=None
            switched=None
            partial=None
            rev_lst=[]
                        
            svnver=self._env.WhereIs('svnversion')
            if svnver is None:
                svnver=self._env.WhereIs('svnversion',os.environ['PATH'])
            
            data=self.command_output('"%s"'%svnver)
            if data:
                data=data.strip('\n\r\t ')
                tmp=data.split(':')
                if data =='exported':
                    pass
                elif len(tmp)==1:
                    try:
                        rev_lst.append(int(tmp[0]))
                    except ValueError:
                        try:
                            rev_lst.append(int(tmp[0][:-1]))
                            if tmp[0][-1]=='M':
                                modified=True
                            elif tmp[0][-1]=='S':
                                switched=True
                            elif tmp[0][-1]=='P':
                                partial=True
                        except ValueError:
                            rev_lst.append(int(tmp[0][:-2]))
                            if tmp[0][-1]=='M' or tmp[0][-2]=='M':
                                modified=True
                            elif tmp[0][-1]=='S' or tmp[0][-2]=='S':
                                switched=True
                            elif tmp[0][-1]=='P' or tmp[0][-2]=='P':
                                partial=True
                else:
                    for i in tmp:
                        try:
                            rev_lst.append(int(i))
                        except ValueError:
                            try:
                                rev_lst.append(int(i[:-1]))
                                if i[0][-1]=='M':
                                    modified=True
                                elif i[0][-1]=='S':
                                    switched=True
                                elif i[0][-1]=='P':
                                    partial=True
                            except ValueError:
                                rev_lst.append(int(i[:-2]))
                                if i[-1]=='M' or i[-2]=='M':
                                    modified=True
                                elif i[-1]=='S' or i[-2]=='S':
                                    switched=True
                                elif i[-1]=='P' or i[-2]=='P':
                                    partial=True
                    
       
            #get the path
            data=self.command_output('"%s" info %s'%(svn.svnpath,self.CheckOutDir))
            if data:
                data=data.replace('\r\n','\n')
                tmp=data.split('\n')
                for i in tmp:
                    if i.startswith('URL: '):
                        server=i[5:]
                    elif i.startswith('Repository Root: '):
                        root=i[len('Repository Root: '):]
                        
            self._disk_data={
                'revision':rev_lst,
                'modified':modified,
                'switched':switched,
                'partial':partial,
                'server':server,
                'root':root
            }
        return self._disk_data
           
            
# add configuartion varaible needed for part
api.register.add_variable('SVN_SERVER','','Value of SVN server to use')
api.register.add_list_variable('SVN_FLAGS',['--non-interactive'],'Flags to use for the svn call')
api.register.add_bool_variable('UPDATE_FROM_SVN',False,'Controls is Part will only update from SVN servers')
#api.register.add_variable('SVN_REVISION',None,'Value of SVN revision to checkout, None mean latest' )
api.register.add_variable('VCS_SVN_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')


api.register.add_global_object('VcsSvn',svn)
