'''
This file contains all code related to the Version controls system objects

'''

import common
import subprocess
import os,sys,shutil,filecmp,time,stat
import SCons.Script 

SCons.Script.Alias('extract_sources')


def process_vcs(env,vcs_type,part_file):
#output=env["PART_LOG_MAPPER"]
    # see if we have a VCS_type to process
    if vcs_type is None:
        # have none just return the orginal file name as is
        return part_file
    def_env=SCons.Script.DefaultEnvironment()
    rpt=def_env['PARTS_REPORTER']
    # we are here we have soem sort of VCS object to process
    # check to see if the file exists
    if vcs_type.FileExists(env,part_file):
        #this file exists. so we check to see if the user wants the sources updated
        if env['UPDATE_ALL']==True or vcs_type.NeedsUpdate(env)==True:
            # Flags had been set for this object to update
            ret=vcs_type.Update(env)
            if ret:
                rpt.part_error(env,"Failure detected during updating sources")
                env.Exit(100+ret)
    else:
        if env['UPDATE_ALL']==False or vcs_type.NeedsUpdate(env)==False:
            # don't have the file and they did not ask to get it
            # so we report a message and do a forced checkout
            rpt.part_warning(env,"Sources do not seem to exist, and no update flags given. Doing forced checkout!",)
        ret=vcs_type.CheckOut(env)
        if ret:
            rpt.part_error(env,"Failure detected during checkout sources")
            env.Exit(100+ret)
    return vcs_type.PartFileName(env,part_file)
            
            

##def process_vcs(env,name,part_file,vcs_type):
##    '''
##    This function is called by parts to allow process of any version control
##    system logic. This function will check setting to see if it need to process
##    and VCS objects, given that one is defined. It will returns the modifed parts
##    file name based on it location it would exist in the repository area we 
##    copied/checked out to.    
##    '''
##    # we do some setup work 
##    # here we get the check out directory
##    #########################
##    node=env.Dir(env.subst('$CHECK_OUT_DIR')).path
##    out_dir=node.path
##    node=node.File(part_file)#,env.subst('$CHECK_OUT_DIR'))
##    retf=node.path
##    filename=node.abspath
##    ######################### with
##    filename = vcs.get_filename(env)
##    # if no vcs_type object is set we just return orginal file name, as we have
##    # no repositories to access
##    if vcs_type==None:
##        return part_file
##    # if the parts_file already exists, that implies the out_dir is in place; if
##    # they don't ask us to do anything, we assume the sources are correctly
##    # checked out and the user does not want us to update at all
##    elif (env['UPDATE_ALL']==False and
##          env['UPDATE_FROM_SVN']==False and
##          os.path.exists(filename)==True):
##        return retf
##    # it is more complicated if the parts_file already exists (which implies
##    # out_dir exists) and they ask us to do something, so defer that while we
##    # handle the simpler case of there not being a parts file
##    elif os.path.exists(filename)==False:
##        if (env['UPDATE_ALL']==False and
##            env['UPDATE_FROM_SVN']==False and
##            env["PARTS_MODE"]=='build'):
##            # print message on why we ignored the update flags
##            print "Warning! Sources do not seem to exist, but no update flags given."
##            print "Overriding flags to get sources."
##            # given that the parts file doesn't exist, we either have to force
##            # an update (regardless of vcs_type) or we have to checkout clean
##            if os.path.exists(out_dir):
##                ret = vcs_type.update_cmd(out_dir,env,name,force=True)
##            else:
##                ret = vcs_type.checkout_cmd(out_dir,env,name)
##            if ret == False:
##                print "Failure detected during checkout/update"
##                print "You may need to manually delete the directory",out_dir
##                env.Exit(127)
##            return retf
##    
##    # if we get here we should let the VCS types process the checkout/update
##    # based on their type, whether the path already exists, and the flags set
##    if vcs_type(out_dir,env,name)==False:
##        print "Failure detected during checkout/update"
##        print "You may need to manually delete the directory",out_dir
##        env.Exit(126)
##    # set directory for Cleaning later
##    
##    return retf

def SysCall (cmdStr):    
    '''
    This internal call is to help with making a system call and printing 
    basic error messages
    '''
    
    #currentDir = os.getcwd ()
    #print currentDir + '> ' + cmdStr
    print cmdStr
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
            print 'Error: The command "' + cmdStr + '" returned ' + str (ret)
            return False
        else:
            return True
    except:
        print 'Error: exception encountered' #, sys.exc_type, sys.exc_value
        return False

class vcs:
    ''' 
    This object is the base for all vcs based objects. It provides base implementation
    and interface functionality needed for all VCS objects
    '''
    def __init__(self,repository,server=None):
        if server is not None and server[-1]!='/':
            server+='/'
        self.repos=repository
        self.server=server

    def __call__(self,out_dir,env,name):
        if common.g_part_mode=='clean':
            self.clean_step(out_dir)
            ret = True
        elif os.path.exists(out_dir):
            ret = self.update_cmd(out_dir,env,name,force=False)
        else:
            ret = self.checkout_cmd(out_dir,env,name)
        return ret

    def full_path(self,env):
        return os.path.join(self.default_server(env),self.repos).replace('\\','/')
        
    def clean_step(self,out_dir):
        #normally does nothing, but in special case permission might need to be set
        pass

    def update_cmd(self,out_dir,env,name,force=False):
        # this is what would be called for any updating of the location
        # assume something already exists
        pass
    def checkout_cmd(self,out_dir,env,name):
        # this is be called if the source has to be retrieved
        # assumes the data does not exist locally yet
        pass

    def Update(self,env):
        def_env=SCons.Script.DefaultEnvironment()
        output=env["PART_LOG_MAPPER"]
        rpt=def_env['PARTS_REPORTER']
        id=output.TaskStart("Updating Sources\n")
        cmd=self.update_cmd(env,env.Dir(env.subst('$CHECK_OUT_DIR')).path)
        ret=SysCall(cmd)
        if ret:
            # we had some failure
            rpt.part_error(env,'The command "' + cmdStr + '" returned [ ' + str (ret)+' ]')
        #all ends well
        output.TaskEnd(id,ret)
        return ret

    def CheckOut(self,env):
        def_env=SCons.Script.DefaultEnvironment()
        output=env["PART_LOG_MAPPER"]
        rpt=def_env['PARTS_REPORTER']
        alias=env['PART_ALIAS']
        id=output.TaskStart("Checking out Sources for %s\n"%(alias))
        cmd=self.update_cmd(env,env.Dir(env.subst('$CHECK_OUT_DIR')).path)
        ret=SysCall(cmd)
        if ret:
            # we had some failure
            rpt.part_error(env,'The command "' + cmdStr + '" returned [ ' + str (ret)+' ]')
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
            rev_string = ' -r ' + self.revision + ' '
        elif env['SVN_REVISION'] is not None:
            rev_string = ' -r ' + env['SVN_REVISION'] + ' '
        return "svn switch --non-interactive"+rev_string+self.full_path(env)+' "'+out_dir+'"'
        
    def checkout_cmd(self,env,out_dir):
        rev_string = ' '
        if self.revision != None:
            rev_string = ' -r ' + self.revision + ' '
        elif env['SVN_REVISION'] is not None:
            rev_string = ' -r ' + env['SVN_REVISION'] + ' '
        return "svn checkout --non-interactive"+rev_string+self.full_path(env)+' "'+out_dir+'"'
        
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
        return opt1==True or opt2==True or vcs.NeedsUpdate(self,env)
    
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

class vcs_Prebuilts(vcs):
    def default_server(self,env):
        if self.server is not None:
            return self.server
        return env['PREBUILT_SERVER']
    
    def Update(self,env,out_dir):
        # we get here because out_dir already exists but the part_file doesn't
        # in which case we should proceed, or else because out_dir already
        # exists and they asked us to do something ... if UPDATE_FROM_SVN only,
        # we don't want to do anything for PRE-BUILTS!
        if force==False and env['UPDATE_ALL']==False:
            return True
        print 'Updating Prebuilts from ' + self.full_path() + ' to ' + out_dir
        try: 
            copier = PyRobocopier ()
            copier.parse_args ([self.full_path(env), out_dir, '-s', '-p', '-f'])
            copier.do_work ()
        except Exception,e:
            print e
            return False
        
        return True
    
    def CheckOut(self,env,out_dir):
        #print 'Copying Prebuilts from ' + self.default_server(env)+self.repos + ' to ' + out_dir
        try:
            p=os.path.normpath(self.full_path(env))
            if os.path.exists(p):
                print 'Copying Prebuilts from ' + p + ' to ' + out_dir
            shutil.copytree (p, out_dir)
        except Exception,e:
            print e
            return False
        
        return True
        
class VcsUsePriorPart(vcs):
    def __init__(self,alias):
        vcs.__init__(self,None,None)
        self.alias=alias

    def Update(self,env):
        return 0

    def CheckOut(self,env):
        return 0

    def PartFileName(self,env,file):
        # get current Alias
        talias=env['PART_ALIAS']
        #set Alias we are mapping to
        env['PART_ALIAS']=self.alias
        env['ALIAS']=self.alias
        #get information
        tmp=env.subst('$CHECK_OUT_DIR')
        ret=env.Dir(tmp).File(file).abspath
        #reset the alias information
        env['PART_ALIAS']=talias
        env['ALIAS']=talias
        return ret
        
    def FileExists(self,env,file):
        return os.path.exists(self.PartFileName(env,file))

    def NeedsUpdate(self,env):
        return False
            

""" The following class was copied from pyrobocopy.py -

    Version: 1.0
    
    Report the difference in content
    of two directories, synchronize or
    update a directory from another, taking
    into account time-stamps of files etc.

    By Anand B Pillai 

    (This program is inspired by the windows
    'Robocopy' program.)

    Mod  Nov 11 Rewrote to use the filecmp module.

Pyrobocopy: Command line directory diff, synchronization, update & copy

Author: Anand Pillai

Usage: %s <sourcedir> <targetdir> Options

Main Options:\n
\t-d --diff         - Only report difference between sourcedir and targetdir
\t-s, --synchronize - Synchronize content between sourcedir and targetdir
\t-u, --update      - Update existing content between sourcedir and targetdir

Additional Options:\n
\t-p, --purge       - Purge files when synchronizing (does not purge by default).
\t-f, --force       - Force copying of files, by trying to change file permissions.
\t-n, --nodirection - Update files in source directory from target
\t                    directory (only updates target from source by default).
\t-c, --create      - Create target directory if it does not exist (By default,
\t                    target directory should exist.)
\t-m, --modtime     - Only compare file's modification times for an update (By default,
\t                    compares source file's creation time also).
"""                   


class PyRobocopier:
    """ An advanced directory synchronization, updation
    and file copying class """

    prog_name = "pyrobocopy.py"
    
    def __init__(self):

        self.__dir1 = ''
        self.__dir2 = ''
        self.__dcmp = None
        
        self.__copyfiles = True
        self.__forcecopy = False
        self.__copydirection = 0
        self.__updatefiles = True
        self.__creatdirs = True
        self.__purge =False
        self.__maketarget =False
        self.__modtimeonly =False
        self.__mainfunc = None
        
        # stat vars
        self.__numdirs =0
        self.__numfiles =0
        self.__numdelfiles =0
        self.__numdeldirs =0     
        self.__numnewdirs =0
        self.__numupdates =0
        self.__starttime = 0.0
        self.__endtime = 0.0
        
        # failure stat vars
        self.__numcopyfld =0
        self.__numupdsfld =0
        self.__numdirsfld =0
        self.__numdelffld  =0
        self.__numdeldfld  =0

    def parse_args(self, arguments):
        """ Parse arguments """
        
        import getopt

        shortargs = "supncm"
        longargs = ["synchronize=", "update=", "purge=", "nodirection=", "create=", "modtime="]

        try:
            optlist, args = getopt.getopt( arguments, shortargs, longargs )
        except getopt.GetoptError, e:
            print e
            return None

        allargs = []
        if len(optlist):
            allargs = [x[0] for x in optlist]
            
        allargs.extend( args )
        self.__setargs( allargs )
            
    def __setargs(self, argslist):
        """ Sets internal variables using arguments """
        
        for option in argslist:
            if option.lower() in ('-s', '--synchronize'):
                self.__mainfunc = self.synchronize
            elif option.lower() in ('-u', '--update'):
                self.__mainfunc = self.update
            elif option.lower() in ('-d', '--diff'):
                self.__mainfunc = self.dirdiff
            elif option.lower() in ('-p', '--purge'):
                self.__purge = True
            elif option.lower() in ('-n', '--nodirection'):
                self.__copydirection = 2
            elif option.lower() in ('-f', '--force'):
                self.__forcecopy = True
            elif option.lower() in ('-c', '--create'):
                self.__maketarget = True
            elif option.lower() in ('-m', '--modtime'):
                self.__modtimeonly = True                            
            else:
                if self.__dir1=='':
                    self.__dir1 = option
                elif self.__dir2=='':
                    self.__dir2 = option
                
        if self.__dir1=='' or self.__dir2=='':
            sys.exit("Argument Error: Directory arguments not given!")
        if not os.path.isdir(self.__dir1):
            sys.exit("Argument Error: Source directory does not exist!")
        if not self.__maketarget and not os.path.isdir(self.__dir2):
            sys.exit("Argument Error: Target directory %s does not exist! (Try the -c option)." % self.__dir2)
        if self.__mainfunc is None:
            sys.exit("Argument Error: Specify an action (Diff, Synchronize or Update) ")

        self.__dcmp = filecmp.dircmp(self.__dir1, self.__dir2)

    def do_work(self):
        """ Do work """

        self.__starttime = time.time()
        
        if not os.path.isdir(self.__dir2):
            if self.__maketarget:
                print 'Creating directory', self.__dir2
                try:
                    os.makedirs(self.__dir2)
                except Exception, e:
                    print e
                    return None

        # All right!
        self.__mainfunc()
        self.__endtime = time.time()
        
    def __dowork(self, dir1, dir2, copyfunc = None, updatefunc = None):
        """ Private attribute for doing work """
        
        #print 'Source directory: ', dir1, ':' ### Uncomment if you want to
                                               ### see the tree walked

        self.__numdirs += 1
        self.__dcmp = filecmp.dircmp(dir1, dir2)
        
        # Files & directories only in target directory
        if self.__purge:
            for f2 in self.__dcmp.right_only:
                fullf2 = os.path.join(dir2, f2)
                print 'Deleting ',fullf2
                try:
                    if os.path.isfile(fullf2):
                        
                        try:
                            os.remove(fullf2)
                            self.__numdelfiles += 1
                        except OSError, e:
                            print e
                            self.__numdelffld += 1
                    elif os.path.isdir(fullf2):
                        try:
                            shutil.rmtree( fullf2, True )
                            self.__numdeldirs += 1
                        except shutil.Error, e:
                            print e
                            self.__numdeldfld += 1
                                
                except Exception, e: # of any use ?
                    print e
                    continue


        # Files & directories only in source directory
        for f1 in self.__dcmp.left_only:
            try:
               st = os.stat(os.path.join(dir1, f1))
            except os.error:
                continue

            if stat.S_ISREG(st.st_mode):
                if copyfunc: copyfunc(f1, dir1, dir2)
            elif stat.S_ISDIR(st.st_mode):
                fulld1 = os.path.join(dir1, f1)
                fulld2 = os.path.join(dir2, f1)
                
                if self.__creatdirs:
                    try:
                        # Copy tree
                        print 'Copying tree', fulld2
                        shutil.copytree(fulld1, fulld2)
                        self.__numnewdirs += 1
                        print 'Done.'
                    except shutil.Error, e:
                        print e
                        self.__numdirsfld += 1
                        
                        # jump to next file/dir in loop since this op failed
                        continue

                # Call tail recursive
                # if os.path.exists(fulld2):
                #    self.__dowork(fulld1, fulld2, copyfunc, updatefunc)

        # common files/directories
        for f1 in self.__dcmp.common:
            try:
                st = os.stat(os.path.join(dir1, f1))
            except os.error:
                continue

            if stat.S_ISREG(st.st_mode):
                if updatefunc: updatefunc(f1, dir1, dir2)
            elif stat.S_ISDIR(st.st_mode):
                fulld1 = os.path.join(dir1, f1)
                fulld2 = os.path.join(dir2, f1)
                # Call tail recursive
                self.__dowork(fulld1, fulld2, copyfunc, updatefunc)
                

    def __copy(self, filename, dir1, dir2):
        """ Private function for copying a file """

        # NOTE: dir1 is source & dir2 is target
        if self.__copyfiles:

            print 'Copying file', filename, dir1, dir2
            try:
                if self.__copydirection== 0 or self.__copydirection == 2:  # source to target
                    
                    if not os.path.exists(dir2):
                        if self.__forcecopy:
                            os.chmod(os.path.dirname(dir2), 0777)
                        try:
                            os.makedirs(dir1)
                        except OSError, e:
                            print e
                            self.__numdirsfld += 1
                        
                    if self.__forcecopy:
                        os.chmod(dir2, 0777)

                    sourcefile = os.path.join(dir1, filename)
                    try:
                        shutil.copy(sourcefile, dir2)
                        self.__numfiles += 1
                    except (IOError, OSError), e:
                        print e
                        self.__numcopyfld += 1
                    
                elif self.__copydirection==1 or self.__copydirection == 2: # target to source 

                    if not os.path.exists(dir1):
                        if self.__forcecopy:
                            os.chmod(os.path.dirname(dir1), 0777)

                        try:
                            os.makedirs(dir1)
                        except OSError, e:
                            print e
                            self.__numdirsfld += 1                          

                    targetfile = os.path.abspath(os.path.join(dir1, filename))
                    if self.__forcecopy:
                        os.chmod(dir1, 0777)

                    sourcefile = os.path.join(dir2, filename)
                    
                    try:
                        shutil.copy(sourcefile, dir1)
                        self.__numfiles += 1
                    except (IOError, OSError), e:
                        print e
                        self.__numcopyfld += 1
                    
            except Exception, e:
                print 'Error copying  file', filename, e

    def __cmptimestamps(self, filest1, filest2):
        """ Compare time stamps of two files and return True
        if file1 (source) is more recent than file2 (target) """

        return ((filest1.st_mtime > filest2.st_mtime) or \
                   (not self.__modtimeonly and (filest1.st_ctime > filest2.st_mtime)))
    
    def __update(self, filename, dir1, dir2):
        """ Private function for updating a file based on
        last time stamp of modification """

        #print 'Updating file', filename ### NOPE; just checking now; Will
                                         ### print below if we REALLY update
        
        # NOTE: dir1 is source & dir2 is target        
        if self.__updatefiles:

            file1 = os.path.join(dir1, filename)
            file2 = os.path.join(dir2, filename)

            try:
                st1 = os.stat(file1)
                st2 = os.stat(file2)
            except os.error:
                return -1

            # Update will update in both directions depending
            # on the timestamp of the file & copy-direction.

            if self.__copydirection==0 or self.__copydirection == 2:

                # Update file if file's modification time is older than
                # source file's modification time, or creation time. Sometimes
                # it so happens that a file's creation time is newer than it's
                # modification time! (Seen this on windows)
                if self.__cmptimestamps( st1, st2 ):
                    print 'Updating file ', file2 # source to target
                    try:
                        if self.__forcecopy:
                            os.chmod(file2, 0666)

                        try:
                            shutil.copy(file1, file2)
                            self.__numupdates += 1
                            return 0
                        except (IOError, OSError), e:
                            print e
                            self.__numupdsfld += 1
                            return -1

                    except Exception, e:
                        print e
                        return -1

            elif self.__copydirection==1 or self.__copydirection == 2:

                # Update file if file's modification time is older than
                # source file's modification time, or creation time. Sometimes
                # it so happens that a file's creation time is newer than it's
                # modification time! (Seen this on windows)
                if self.__cmptimestamps( st2, st1 ):
                    print 'Updating file ', file1 # target to source
                    try:
                        if self.__forcecopy:
                            os.chmod(file1, 0666)

                        try:
                            shutil.copy(file2, file1)
                            self.__numupdates += 1
                            return 0
                        except (IOError, OSError), e:
                            print e
                            self.__numupdsfld += 1
                            return -1
                        
                    except Exception, e:
                        print e
                        return -1

        return -1

    def __dirdiffandcopy(self, dir1, dir2):
        """ Private function which does directory diff & copy """
        self.__dowork(dir1, dir2, self.__copy)

    def __dirdiffandupdate(self, dir1, dir2):
        """ Private function which does directory diff & update  """        
        self.__dowork(dir1, dir2, None, self.__update)

    def __dirdiffcopyandupdate(self, dir1, dir2):
        """ Private function which does directory diff, copy and update (synchro) """               
        self.__dowork(dir1, dir2, self.__copy, self.__update)

    def __dirdiff(self):
        """ Private function which only does directory diff """

        if self.__dcmp.left_only:
            print 'Only in', self.__dir1
            for x in self.__dcmp.left_only:
                print '>>', x

        if self.__dcmp.right_only:
            print 'Only in', self.__dir2
            for x in self.__dcmp.right_only:
                print '<<', x

        if self.__dcmp.common:
            print 'Common to', self.__dir1,' and ',self.__dir2
            print
            for x in self.__dcmp.common:
                print '--', x
        else:
            print 'No common files or sub-directories!'

    def synchronize(self):
        """ Synchronize will try to synchronize two directories w.r.t
        each other's contents, copying files if necessary from source
        to target, and creating directories if necessary. If the optional
        argument purge is True, directories in target (dir2) that are
        not present in the source (dir1) will be deleted . Synchronization
        is done in the direction of source to target """

        self.__copyfiles = True
        self.__updatefiles = True
        self.__creatdirs = True
        self.__copydirection = 0

        print 'Synchronizing directory', self.__dir2, 'with', self.__dir1 ,'\n'
        self.__dirdiffcopyandupdate(self.__dir1, self.__dir2)

    def update(self):
        """ Update will try to update the target directory
        w.r.t source directory. Only files that are common
        to both directories will be updated, no new files
        or directories are created """

        self.__copyfiles = False
        self.__updatefiles = True
        self.__purge = False
        self.__creatdirs = False

        print 'Updating directory', self.__dir2, 'from', self.__dir1 , '\n'
        self.__dirdiffandupdate(self.__dir1, self.__dir2)

    def dirdiff(self):
        """ Only report difference in content between two
        directories """

        self.__copyfiles = False
        self.__updatefiles = False
        self.__purge = False
        self.__creatdirs = False
        self.__updatefiles = False
        
        print 'Difference of directory ', self.__dir2, 'from', self.__dir1 , '\n'
        self.__dirdiff()
        
    def report(self):
        """ Print report of work at the end """

        # We need only the first 4 significant digits
        tt = (str(self.__endtime - self.__starttime))[:4]
        
        print '\nPython robocopier finished in',tt, 'seconds.'
        print self.__numdirs, 'directories parsed,',self.__numfiles, 'files copied.'
        if self.__numdelfiles:
            print self.__numdelfiles, 'files were purged.'
        if self.__numdeldirs:
            print self.__numdeldirs, 'directories were purged.'
        if self.__numnewdirs:
            print self.__numnewdirs, 'directories were created.'
        if self.__numupdates:
            print self.__numupdates, 'files were updated by timestamp.'

        # Failure stats
        print '\n'
        if self.__numcopyfld:
            print self.__numcopyfld, 'files could not be copied.'
        if self.__numdirsfld:
            print self.__numdirsfld, 'directories could not be created.'
        if self.__numupdsfld:
            print self.__numupdsfld, 'files could not be updated.'
        if self.__numdeldfld:
            print self.__numdeldfld, 'directories could not be purged.'
        if self.__numdelffld:
            print self.__numdelffld, 'files could not be purged.'


# add configuartion varaible needed for part
common.AddVariable('SVN_SERVER','','Value of SVN server to use')
common.AddVariable('CVS_SERVER','','Value of CVS server to use')
common.AddVariable('PREBUILT_SERVER','','Path to location of prebuilt data')
#common.AddVariable('PROCESS_VCS',False) # deprecated; use UPDATE_ALL
common.AddBoolVariable('UPDATE_ALL',False,'Controls if Parts will update source from servers')
common.AddBoolVariable('UPDATE_FROM_SVN',False,'Controls is Part will only update from SVN servers')
common.AddVariable('SVN_REVISION',None,'Value of SVN revision to checkout, None mean latest' )
common.AddVariable('CHECK_OUT_ROOT','#repository','Root directory to place checked out data')
common.AddVariable('CHECK_OUT_DIR','$CHECK_OUT_ROOT/$ALIAS','Full path used for any given checked out item')

common.add_global_value('VcsSvn',vcs_svn)
common.add_global_value('VcsCvs',vcs_cvs)
common.add_global_value('VcsPreBuilt',vcs_Prebuilts)
common.add_global_value('VcsUsePriorPart',VcsUsePriorPart)



