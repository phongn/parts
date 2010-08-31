## this file contains functions I overide in SCons for various reasons
## most of these are just function proxies to add internal like functionality
## where I need it. Hopefully most of these items will move into SCons in some form

import SCons.Script
import SCons.Util
import SCons.Environment
import os
import sys
import thread


from SCons.Script import _SConscript 
import SCons.Script.Main

if sys.platform=='win32':
    #This allow us to up file in a non-exclusive mode
    import ctypes
    import __builtin__
    import msvcrt

    _orginial_file = __builtin__.file
    _orginial_open = __builtin__.open
    
    # this import to stop SCons from doing what it is doing with open/file
    import SCons.Platform.win32

    FILE_SHARE_READ=1
    FILE_SHARE_WRITE=2
    FILE_SHARE_DELETE=4

    GENERIC_READ =-0x80000000
    GENERIC_WRITE=0x40000000

    CREATE_ALWAYS=2
    OPEN_EXISTING=3
    OPEN_ALWAYS=4
    TRUNCATE_EXISTING=5

    
    def get_win32_desired_access(str):
        ret=0
        if str.find('r')!=-1:
            ret=GENERIC_READ
        if str.find('w')!=-1 or str.find('+')!=-1 or str.find('a')!=-1:
            ret=ret|GENERIC_WRITE
            
        return ret

    def get_win32_shared_mode(str):
        ret=FILE_SHARE_DELETE|FILE_SHARE_READ|FILE_SHARE_WRITE
        #if str.find('w')!=-1 or str.find('+')!=-1 or str.find('a')!=-1:
        #    ret=ret|FILE_SHARE_WRITE
        return ret    

    def get_win32_creation_disposition(str):
        ret=0
        if str.find('w')!=-1 or str.find('+')!=-1:
            ret=CREATE_ALWAYS
        elif str.find('r')!=-1:
            ret=OPEN_EXISTING
        else:
            ret=OPEN_ALWAYS
            
        return ret
    
    def shared_open(filename, mode='r', bufsize=-1):
        # this is sort of ugly
        
        #sys.__stdout__.write("\n **** "+str(filename)+" "+ str(mode)+" "+str(bufsize)+'\n')
        fd=ctypes.windll.kernel32.CreateFileW(unicode(filename),
                    get_win32_desired_access(mode),# read, write modes
                    get_win32_shared_mode(mode),# add share delete
                    None, #default securtity
                    get_win32_creation_disposition(mode), #If we create the file or not
                    128, # normal attribute.. FILE_ATTRIBUTE_NORMAL
                    0 # no Template
                )
        if fd == -1:
            
            raise IOError,ctypes.FormatError(ctypes.GetLastError())
        # not sure if I should modify flags passed here, 
        # as the next call will get them
        if mode.find('b') != -1:
            tmp=msvcrt.open_osfhandle(fd,os.O_BINARY) 
        else:
            tmp=msvcrt.open_osfhandle(fd,os.O_TEXT) 
        
        f=os.fdopen(tmp,mode,bufsize)
        
        return f
        
    __builtin__.file=shared_open
    __builtin__.open=shared_open
    _SConscript.open=_orginial_open
    
    # ideally this should be done with a reimpl of SCons.Node.FS.LocalFS
    def win32_rm(path):
        r=ctypes.windll.kernel32.DeleteFileW(unicode(path))
        if r ==0 :
            raise OSError,ctypes.FormatError(ctypes.GetLastError())
   
    os.remove=win32_rm
    os.unlink=win32_rm

# this class allows us to add object varible that get a reference to the env
# that holds it
class bindable(object):
    pass

import common

OrigSConscript_exception=_SConscript.SConscript_exception
def PartSConscript_exception(file=None):
    ''' this is silly in general, but is done to allow the remapping of stream 
    to work better as the orginal code get the stream before I remap it as it is
    a default option. This prevents sys.stderr from being used by have my 
    stderr used be used.'''
    if file==None:
        file=sys.stderr
    OrigSConscript_exception(file)
_SConscript.SConscript_exception=PartSConscript_exception

def PartsClone(self, tools=[], toolpath=None, parse_flags = None, **kw):
    clone_env=self._orig_Clone(tools,toolpath,parse_flags,**kw)
    #rebind and bindable 
    clone_env.bindable_vars=[]
    if hasattr(self, 'bindable_vars'):
        for i in self.bindable_vars:
            clone_env.bindable_vars.append(i)
            clone_env[i]=clone_env[i]._rebind(clone_env,i)
    return clone_env
        

def Parts__setitem__(self,key,val):
    if getattr(self,'_log_keys',False):
        if self.has_key(key)==False:
            pobj=common.g_engine._part_manager._from_env(self)
            if pobj and common.is_string(val):
                pobj._env_exports[key]=val
    self._orig__setitem__(key,val)
    if isinstance(val,bindable):
        try:
            self.bindable_vars.append(key)
        except:
            self.bindable_vars=[key]
        val._bind(self,key)

def Parts__getitem__(self,key):
    return self._orig__getitem__(key)
    


class PartPathDirsWrapper:
    """This is a wrapper class to work around a "bug" with the scanner in that
    it tries to delay expand variables which might modify the Env. This
    allows use to expand the area in the env before it tries to create the tuple
    list of paths that it will use to scan with. """
    def __init__(self, obj):
        self.obj = obj
        #print "$$$",obj.variable
    def __call__(self, env, dir, target=None, source=None, argument=None):
        import mappers
        prop_lst=env.get(self.obj.variable,[])
        if prop_lst!=[]:
            ret=mappers.sub_lst(env,prop_lst,thread.get_ident())
            env[self.obj.variable]=ret
        #print 'Scanner', target[0]        
        return self.obj(env,dir,target,source,argument)


def Scanner_override():
    ## this is for fixing an issue with the scanners in which one item in a env
    ## does not have the $vars fully expanded, which causes an issue with in the
    ## dependency tree. This leads to a false rebuild of few files
    for k in SCons.Tool.SourceFileScanner.function.keys():
        if isinstance(SCons.Tool.SourceFileScanner.function[k].path_function,SCons.Scanner.FindPathDirs):
            SCons.Tool.SourceFileScanner.function[k].path_function=PartPathDirsWrapper(
            SCons.Tool.SourceFileScanner.function[k].path_function)

cc=[]
cct=[]


Orig_BuildWrapper=SCons.Environment.BuilderWrapper
class Parts_BuilderWrapper(Orig_BuildWrapper):

    def __call__(self, target=None, source=SCons.Environment._null, *args, **kw):
        
        # self.object should be the env value
        pobj=common.g_engine._part_manager._from_env(self.object)   
        
        # clean up source value to make it a list as the builder would expect it
        # this help me latter in dealing with the values myself
        # we don't make them real nodes as we don't know what the builder wants
        if SCons.Util.is_String(source):
            source=[source] # make it a list
        elif source==SCons.Environment._null:
            pass # leave it alone
        elif SCons.Util.is_List(source):
            # flatten the list
            source = SCons.Util.flatten(source)
            
        
        dup=kw.get("allow_duplicates",False)
        found=False
        if dup:
            #Get info for help store info matches better
            if pobj is not None:
                name=pobj.Name
                srcpath=pobj.SourcePath
            else:
                name=None
                srcpath=None
            # make key
            
            if source==SCons.Environment._null:
                s="_null"
            elif source != []:# SCons.Util.is_List(source):
                s=os.path.split(str(source[0]))[1]
            else:
                s="_null"
                
            
            if target == []:
                key=(srcpath,s,self.name,name)
            else:
                key=(target,s,self.name,name)
            
            #test for match
            if key in cc:
                #print "seen this one!!!!!!!!!!!!!!!!!!!",cc.index(key)
                #print key
                tmp= cct[cc.index(key)]
                found=True
        
        if not found:
            tmp=Orig_BuildWrapper.__call__(self,target, source, *args, **kw)
        
        #take care of resolved target information.
        if dup:
            cc.append(key)
            cct.append(tmp)
            
        #don't add it to the Parts target list if this has no part or
        #if the actions here are part of a AutoConfigure set of calls
        if pobj is not None and 'SConfSourceBuilder' not in self.object['BUILDERS']:
            pobj._target_files.update(tmp)
        else:
            print tmp[0], 'missing'
        return tmp

try:
    SCons.Util._semi_deepcopy_inst
    def my_semi_deepcopy(x):
        ''' fixes issues with deepcopy'''
        copier = SCons.Util._semi_deepcopy_dispatch.get(type(x))
        if copier:
            return copier(x)
        else:
            return SCons.Util._semi_deepcopy_inst(x)

    SCons.Util.semi_deepcopy=my_semi_deepcopy
except AttributeError:
    pass


# overides for better error reporting

def Parts_find_deepest_user_frame(tb):
    """
    Find the deepest stack frame that is not part of SCons.

    Input is a "pre-processed" stack trace in the form
    returned by traceback.extract_tb() or traceback.extract_stack()
    """
    
    tb.reverse()

    # find the deepest traceback frame that is not part
    # of SCons:
    ftmp = SCons.Script.GetOption("file")
    if len(ftmp) == 0:
        ftmp=['sconstruct']
        
    def list_endwith(str, lst):
        str=str.lower()
        for l in lst:
            l=l.lower()
            if str.endswith(l):
                return True
        return False
    #print len(tb)
    for frame in tb:
        filename = frame[0]
        #print filename
        if filename.find(os.sep+'SCons'+os.sep) == -1 and list_endwith(filename,['.parts','.part']) == True:
            return frame
        elif list_endwith(filename,ftmp):
            return lastframe
        lastframe=frame
    #print "->",tb[0]
    return tb[0]

SCons.Script.Main.find_deepest_user_frame=Parts_find_deepest_user_frame

import poptions

scons_DefaultEnvironment=SCons.Script.DefaultEnvironment

def Part_DefaultEnvironment(*args,**kw):
    if common.g_engine is None or common.g_engine.def_env is None:
        return scons_DefaultEnvironment(*args,**kw)
    try:
        if poptions.SetOptionDefault._modified==False:
            return Part_DefaultEnvironment._cache
    except AttributeError:
        pass
    #remake the def env
    common.g_engine._setup_defenv()
    #store in chache
    Part_DefaultEnvironment._cache=common.g_engine.def_env
    poptions.SetOptionDefault._modified=False
    return Part_DefaultEnvironment._cache

SCons.Script.DefaultEnvironment=Part_DefaultEnvironment


# this code overides scons build targets so we can do some processing before 
# Scons tries to build the tree.

import SCons.Script.Main
scons_build_targets = SCons.Script.Main._build_targets


def _build_targets(fs, options, targets, target_top):
    
        # call engine
    if common.g_engine.Process(fs, options, targets, target_top) == False:
        ret= None
    else:
        # call Scons function is there is nothing wrong 
        # with the engine/addin Process call
        ret= scons_build_targets(fs, options, targets, target_top)
        
    return ret

SCons.Script.Main._build_targets = _build_targets


# this overides the builer call so I can get the file that called the builder.
# this allow be a simple test to see what file to check for changes of build
# context

scons_builder=SCons.Builder.Builder

def Part_Builder(**kw):
    common.g_build_context_files.add(sys._getframe(1).f_code.co_filename)
    return scons_builder(**kw)

SCons.Builder.Builder=Part_Builder


from SCons.Script.SConscript import SConsEnvironment

# override Clone to deepcopy bindable objects
SConsEnvironment._orig_Clone=SConsEnvironment.Clone
SConsEnvironment.Clone=PartsClone

# override __setitem__ bind env with bindable objects when set
SConsEnvironment._orig__setitem__=SConsEnvironment.__setitem__
SConsEnvironment.__setitem__=Parts__setitem__

SConsEnvironment._orig__getitem__=SConsEnvironment.__getitem__
SConsEnvironment.__getitem__=Parts__getitem__

# override the builder wrapper to allow us to get the files defined in the scope of a part
SCons.Environment.BuilderWrapper=Parts_BuilderWrapper