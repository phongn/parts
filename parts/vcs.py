'''
This file contains all code related to the Version controls system objects

'''

import common
import subprocess
import os,sys,shutil,filecmp,time,stat
import SCons.Script 
import SCons.Errors
import reporter

SCons.Script.Alias('extract_sources')


def process_vcs(env,vcs_type,part_file):
#output=env["PART_LOG_MAPPER"]
    # see if we have a VCS_type to process
    if vcs_type is None:
        # have none just return the orginal file name as is
        return part_file
    
    # we are here we have soem sort of VCS object to process
    # check to see if the file exists
    vcs_type.UpdateEnv(env)
    if vcs_type.FileExists(env,part_file):
        #this file exists. so we check to see if the user wants the sources updated
        if env['UPDATE_ALL']==True or vcs_type.NeedsUpdate(env)==True:
            # Flags had been set for this object to update
            ret=vcs_type.Update(env)
            if ret:
                reporter.report_error("Failure detected during updating sources")
    else:
        if env['UPDATE_ALL']==False and vcs_type.NeedsUpdate(env)==False:
            # don't have the file and they did not ask to get it
            # so we report a message and do a forced checkout
            reporter.report_warning("Sources do not seem to exist, and no update flags given, such as UPDATE_ALL=True\n\
 Automatically updating component.",show_stack=False)
            
        ret=vcs_type.CheckOut(env)
        if ret:
            reporter.report_error("Failure detected during checkout sources")
            
    return vcs_type.PartFileName(env,part_file)
            
            

def SysCall (cmdStr):    
    '''
    This internal call is to help with making a system call and printing 
    basic error messages
    '''
    
    #currentDir = os.getcwd ()
    #print currentDir + '> ' + cmdStr
    reporter.print_msg(cmdStr)
    sys.stdout.flush ()
    try: 
        proc = subprocess.Popen (cmdStr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while (proc.poll () == None):
            sys.stdout.write (proc.stdout.readline ())
        sys.stdout.write (proc.stdout.read ())
        print ''
        ret = proc.returncode
        return ret
        if ret:
            reporter.report_error('The command "' +cmdStr + '" returned ' + str (ret))
        else:
            return True
    except OSError:
        reporter.report_error('Error: exception encountered') #, sys.exc_type, sys.exc_value)
        

class vcs:
    ''' 
    This object is the base for all vcs based objects. It provides base implementation
    and interface functionality needed for all VCS objects
    '''
    def __init__(self,repository,server=None):
        if server is not None and server[-1]!='/':
            server+='/'
        if repository.startswith('/') or repository.startswith('\\'):
            self.repos=repository[1:]
        else:
            self.repos=repository
        self.server=server

    def __call__(self,out_dir,env,name):
        if common.g_part_mode=='clean':
            self.clean_step(out_dir)
            ret = True
        elif os.path.exists(out_dir):
            ret = self.update_cmd(out_dir,env,name)
        else:
            ret = self.checkout_cmd(out_dir,env,name)
        return ret

    def full_path(self,env):
        return os.path.join(self.default_server(env),self.repos).replace('\\','/')
        
    def clean_step(self,out_dir):
        #normally does nothing, but in special case permission might need to be set
        pass

    def update_cmd(self,out_dir,env,name):
        # this is what would be called for any updating of the location
        # assume something already exists
        pass
    def checkout_cmd(self,out_dir,env,name):
        # this is be called if the source has to be retrieved
        # assumes the data does not exist locally yet
        pass

    def Update(self,env):
        output=env["PART_LOG_MAPPER"]
        id=output.TaskStart("Updating Sources\n")
        cmd=self.update_cmd(env,env.Dir(env.subst('$CHECK_OUT_DIR')).path)
        ret=SysCall(cmd)
        if ret:
            # we had some failure
            reporter.report_error('The command "' + cmd + '" returned [ ' + str (ret)+' ]')
        #all ends well
        output.TaskEnd(id,ret)
        return ret

    def CheckOut(self,env):
        output=env["PART_LOG_MAPPER"]
        alias=env['PART_ALIAS']
        id=output.TaskStart("Checking out Sources for %s\n"%(alias))
        cmd=self.checkout_cmd(env,env.Dir(env.subst('$CHECK_OUT_DIR')).path)
        ret=SysCall(cmd)
        if ret:
            # we had some failure
            reporter.report_error('The command "' + cmd + '" returned [ ' + str (ret)+' ]')
        #all ends well
        output.TaskEnd(id,ret)
        return ret

    def PartFileName(self,env,file):
        ret=env.Dir(env.subst('$CHECK_OUT_DIR')).File(file).abspath
        return ret
        
    def FileExists(self,env,file):
        return os.path.exists(self.PartFileName(env,file))

    def NeedsUpdate(self,env):
        alias=env['PART_ALIAS']
        return env.get('UPDATE_'+alias.upper(),None) is not None
    
    def UpdateEnv(self,env):
        ''' 
        Update the with information about the current VCS object
        '''
        env['VCS']=common.namespace(
                TYPE='unknown',
                CHECKOUT_DIR=''
            ) 
    
        

class vcs_svn(vcs):
    def __init__(self,repository,server=None,revision=None):
        self.revision = revision
        vcs.__init__(self,repository,server)
    def default_server(self,env):
        if self.server is not None:
            return self.server
        return env['SVN_SERVER']
    def update_cmd(self,env,out_dir):
        # update command in SVN updates a given location... in reality we may
        # want to say update this area with a different version; the switch
        # command is the more correct option in this case than the update command!

        # we get here because out_dir already exists and they asked us to do
        # something (UPDATE_ALL or UPDATE_FROM_SVN), or because it exists, but
        # the part_file is missing ... in all cases we act the same way
        rev_string = ' '
        if self.revision != None:
            rev_string = '@' + self.revision + ' '
        elif env['SVN_REVISION'] is not None:
            rev_string = '@' + env['SVN_REVISION'] + ' '
        return "svn switch --non-interactive "+self.full_path(env)+rev_string+' "'+out_dir+'"'
        
    def checkout_cmd(self,env,out_dir):
        rev_string = ' '
        if self.revision != None:
            rev_string = '@' + self.revision + ' '
        elif env['SVN_REVISION'] is not None:
            rev_string = '@' + env['SVN_REVISION'] + ' '
        return "svn checkout --non-interactive "+self.full_path(env)+rev_string+' "'+out_dir+'"'
        
    def clean_step(self,out_dir):
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

    def NeedsUpdate(self,env):
        opt1=env.get('UPDATE_FROM_SVN',False)
        opt2=env.get('UPDATE_'+env['PART_ALIAS'].upper(),False)
        opt3=env.get('UPDATE_'+env['SHORT_ALIAS'].upper(),False)
        return opt1==True or opt2==True or opt3==True or vcs.NeedsUpdate(self,env)
    
    def UpdateEnv(self,env):
        ''' 
        Update the with information about the current VCS object
        '''
        env['VCS']=common.namespace(
                TYPE='svn',
                CHECKOUT_DIR='$VCS_SVN_DIR',
            )
    
class vcs_cvs(vcs):
    def default_server(self,env):
        if self.server is not None:
            return self.server
        return env['CVS_SERVER']
    def update_cmd(self,env,out_dir):
        #'cvs -z' + str (cvsCompressLevel) + ' up -d -r ' + componentVersion
        return "echo cvs update FILL IN CODE"
    def checkout_cmd(self,env,out_dir):
        #'cvs -z' + str (cvsCompressLevel) + ' -d:pserver:' + userName + '@' + component.server + ':' 
        #+ component.repos + ' co -d ' + componentVersion + ' -r ' + componentVersion + ' ' + component.path
        return "echo cvs checkout FILL IN CODE"
    
    def UpdateEnv(self,env):
        ''' 
        Update the with information about the current VCS object
        '''
        env['VCS']=common.namespace(
                TYPE='cvs',
                CHECKOUT_DIR='$VCS_CVS_DIR',
            )

class vcs_Prebuilts(vcs):
    def default_server(self,env):
        if self.server is not None:
            return self.server
        return env['PREBUILT_SERVER']
    
    def Update(self,env):
        # we get here because out_dir already exists but the part_file doesn't
        # in which case we should proceed, or else because out_dir already
        # exists and they asked us to do something ... if UPDATE_FROM_SVN only,
        # we don't want to do anything for PRE-BUILTS!
        out_dir=env.Dir(env.subst('$CHECK_OUT_DIR')).path
        p=os.path.normpath(self.full_path(env))
        reporter.print_msg( 'Updating Prebuilts from ' + p + ' to ' + out_dir)
        try:
            shutil.rmtree (out_dir) 
            shutil.copytree (p, out_dir)
        except Exception,e:
            print e
            return 1
        
        return 0
    
    def CheckOut(self,env):
        #print 'Copying Prebuilts from ' + self.default_server(env)+self.repos + ' to ' + out_dir
        out_dir=env.Dir(env.subst('$CHECK_OUT_DIR')).path
        p=os.path.normpath(self.full_path(env))
        reporter.print_msg( 'Copying Prebuilts from ' + p + ' to ' + out_dir)
        try:
            shutil.copytree (p, out_dir)
        except Exception,e:
            print e
            return 1
        
        return 0
    def UpdateEnv(self,env):
        ''' 
        Update the with information about the current VCS object
        '''
        env['VCS']=common.namespace(
                TYPE='prebuilds',
                CHECKOUT_DIR='$VCS_PREBUILDS_DIR',
            )
        
class VcsUsePriorPart(vcs):
    def __init__(self,alias):
        vcs.__init__(self,"",None)
        self.alias=alias

    def Update(self,env):
        return 0

    def CheckOut(self,env):
        return 0

    def PartFileName(self,env,file):
        # get current Alias
        talias=env['PART_ALIAS']
        #set Alias we are mapping to
        env['PART_ALIAS']=env.subst(env.get('ALIAS_PREFIX','')+self.alias+env.get('ALIAS_POSTFIX',''))
        env['ALIAS']=env['PART_ALIAS']
        #get information
        tmp=env.subst('$CHECK_OUT_DIR')
        ret=env.Dir(tmp).File(file).abspath
        #reset the alias information
        env['PART_ALIAS']=talias
        env['ALIAS']=talias
        env['CHECK_OUT_DIR']=tmp
        
        return ret
        
    def FileExists(self,env,file):
        return os.path.exists(self.PartFileName(env,file))

    def NeedsUpdate(self,env):
        return False
    
    def UpdateEnv(self,env):
        ''' 
        Update the with information about the current VCS object
        '''
        # figure out what vcs type other parts is 
        def_env=SCons.Script.DefaultEnvironment()
        alias=env.subst(env.get('ALIAS_PREFIX','')+self.alias+env.get('ALIAS_POSTFIX',''))
        # clone???
        try:
            envt=def_env['PART_INFO'][alias]['ENV']
        except KeyError:
            raise SCons.Errors.UserError('Part %s was not defined before Part %s'%(alias,env['SHORT_ALIAS']))
        try:
            vcsobj=envt['VCS']
            env['VCS']=vcsobj
            env['VCS']['ORGINAL_TYPE']=env['VCS']['TYPE']
            env['VCS']['TYPE']='UsePriorPart'
        except:
            env['VCS']=common.namespace(
                    TYPE='UsePriorPart',
                    CHECKOUT_DIR='$VCS_PREBUILDS_DIR',
                )
            env['VCS']['ORGINAL_TYPE']='Unknown'
            


# add configuartion varaible needed for part
common.AddVariable('SVN_SERVER','','Value of SVN server to use')
common.AddVariable('CVS_SERVER','','Value of CVS server to use')
common.AddVariable('PREBUILT_SERVER','','Path to location of prebuilt data')
#common.AddVariable('PROCESS_VCS',False) # deprecated; use UPDATE_ALL
common.AddBoolVariable('UPDATE_ALL',False,'Controls if Parts will update source from servers')
common.AddBoolVariable('UPDATE_FROM_SVN',False,'Controls is Part will only update from SVN servers')
common.AddVariable('SVN_REVISION',None,'Value of SVN revision to checkout, None mean latest' )
common.AddVariable('CHECK_OUT_ROOT','#vcs','Root directory to place checked out data')
common.AddVariable('CHECK_OUT_DIR','$VCS_DIR','Full path used for any given checked out item')
common.AddVariable('VCS_DIR','$VCS.CHECKOUT_DIR','')
common.AddVariable('VCS_SVN_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')
common.AddVariable('VCS_CVS_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')
common.AddVariable('VCS_PREBUILDS_DIR','${CHECK_OUT_ROOT}/${ALIAS}','Full path used for any given checked out item')

common.add_global_value('VcsSvn',vcs_svn)
common.add_global_value('VcsCvs',vcs_cvs)
common.add_global_value('VcsPreBuilt',vcs_Prebuilts)
common.add_global_value('VcsUsePriorPart',VcsUsePriorPart)



#$CHECK_OUT_ROOT/${PAT_VCS.NAME}${PAT_VCS.STABLE_VERSION.Major()}/${BUILD_BRANCH}