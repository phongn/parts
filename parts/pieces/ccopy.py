
import SCons.Script
import sys
import os
import shutil
import parts.common as common
import parts.node_helpers as node_helpers
import parts.reporter as reporter
import stat

# generic copy builder
if sys.platform == 'win32':
    import ctypes
    def ccopy_hard_soft(dest,source):
        try:
            ctypes.windll.kernel32.CreateHardLinkW(unicode(dest),unicode(source))
        except:
            try:
                # we only deal with files in our cases
                ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dest),unicode(source),0)
            except:
                ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
                if ret==0:
                    raise ctypes.WinError()

    def ccopy_soft_hard(dest,source):    
        try:
            # we only deal with files in our cases
            ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dest),unicode(source),0)
        except:
            try:
                ctypes.windll.kernel32.CreateHardLinkW(unicode(dest),unicode(source))
            except:
                ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
                if ret==0:
                    raise ctypes.WinError()
                
    def ccopy_hard(dest,source):
        try:
            ctypes.windll.kernel32.CreateHardLinkW(unicode(dest),unicode(source))
        except:
            ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
            if ret==0:
                raise ctypes.WinError()
        
    def ccopy_soft(dest,source):
        try:
            # we only deal with files in our cases
            ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dest),unicode(source),0)
        except:
            ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
            if ret==0:
                raise ctypes.WinError()
        
    def ccopy_copy(dest,source):
        ret=ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
        if ret==0:
            raise ctypes.WinError()
else:
    def ccopy_hard_soft(dest,source):
        try:        
            os.link(source,dest)
        except:
            try:
                os.symlink(source,dest)
            except:
                shutil.copy2(source, dest)
                st = os.stat(source)
                os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    def ccopy_soft_hard(dest,source):    
        try:        
            os.symlink(source,dest)
        except:
            try:
                os.link(source,dest)
            except:
                shutil.copy2(source, dest)
                st = os.stat(source)
                os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

        
    def ccopy_hard(dest,source):        
        try:
            os.link(source,dest)
        except:
            shutil.copy2(source, dest)
            st = os.stat(source)
            os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
        
    def ccopy_soft(dest,source):
        try:
            os.symlink(source,dest)
        except:
            shutil.copy2(source, dest)
            st = os.stat(source)
            os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
        
    def ccopy_copy(dest,source):

        shutil.copy2(source, dest)
        st = os.stat(source)
        os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)




def CCopyFuncWrapper(dest, source, env, copyfunc):
    
    if os.path.isdir(source):
        if os.path.exists(dest):
            if not os.path.isdir(dest):
                raise SCons.Errors.UserError, "cannot overwrite non-directory `%s' with a directory `%s'" % (str(dest), str(source))
        else:
            parent = os.path.split(dest)[0]
            if not os.path.exists(parent):
                os.makedirs(parent)
        shutil.copytree(source, dest)
    else:
        copyfunc(dest,source)
        
    return 0

def CCopyFunc(target, source, env, copy_logic):
    
    # get the logger for the given part
    output=env["PART_LOG_MAPPER"]    
    # tell it we are starting a task
    id=output.TaskStart(CCopyStringFunc(target,source,env)+"\n")
        
    assert( len(target) == len(source) ), "\ntarget: %s\nsource: %s" %(map(str, target),map(str, source))
    
    for t, s in zip(target, source):
        #Get info if this should be handled as a symlink
        symlink=env.MetaTagValue(t,'SymLink')
        if symlink is not None:
            # it a symlink so make a new link
            node_helpers.make_link_bf([t],None,env)            
        else: 
            #Do normal copy stuff
            CCopyFuncWrapper(t.get_path(), s.get_path(), env,copy_logic)
    #tell logger the task has end correctly.
    output.TaskEnd(id,0)
    return None

def CCopyStringFunc(target, source, env):
    target = str(target[0])
    source = str(source[0])
    if os.path.isdir(source):
        type = 'directory'
    else:
        type = 'file'
    target_path, target_f = os.path.split(str(target))
    
    return 'Parts: Copying %s: "%s" to "%s" as: "%s"' % (type, source, target_path,target_f)

def CCopyEmit(target, source, env):
    return ([target[0]], [source[0]])


class CCopy(object):
    default=0
    copy=1
    hard_soft_copy=2
    soft_hard_copy=3
    hard_copy=4
    soft_copy=5


def CCopyWrapper(env, target=None, source=None,copy_logic=CCopy.default,**kw):

    target_factory = env.fs
    # test args a little
    try:
        dnodes = env.arg2nodes(target, target_factory.Dir)
    except TypeError:
        reporter.report_error("Target `%s' is a file, but should be a directory.  Perhaps you have the arguments backwards?" % str(dir))
    
    #setup copy function
    if copy_logic == CCopy.default:
        copy_logic=env.get('CCOPY_LOGIC',CCopy.copy) # make fallback a safe one
    if copy_logic == CCopy.copy:
        copy_logic=env.__CCopyBuilderC__
    elif copy_logic == CCopy.hard_soft_copy:
        copy_logic=env.__CCopyBuilderHSC__
    elif copy_logic == CCopy.soft_hard_copy:
        copy_logic=env.__CCopyBuilderSHC__
    elif copy_logic == CCopy.hard_copy:
        copy_logic=env.__CCopyBuilderHC__
    elif copy_logic == CCopy.soft_copy:
        copy_logic=env.__CCopyBuilderSC__
    else:
        copy_logic=env.__CCopyBuilderC__
    
    source=common.make_list(source)
    sources=[]
    
    # workaround to not having symlinks yet
    for s in source:
        tmp=env.arg2nodes(s, env.fs.Entry)
        symlink=None
        if isinstance(s,SCons.Node.FS.File):
            symlink=env.MetaTagValue(s,'SymLink')
        if symlink is not None:
            env.MetaTag(tmp[0],SymLink=symlink)
        sources.extend(tmp)
        
    #sources = env.arg2nodes(source, env.fs.Entry)
    n_targets = []
    for dnode in dnodes:
        for src in sources:
            # Prepend './' so the lookup doesn't interpret an initial
            # '#' on the file name portion as meaning the Node should
            # be relative to the top-level SConstruct directory.
            symlink=env.MetaTagValue(src,'SymLink')
            if symlink is not None:
                e=env.fs.File('.'+os.sep+src.name, dnode)
                env.MetaTag(e,SymLink=symlink)
                env.MetaTag(e,SymLinkMakeDummyFile=env.MetaTagValue(src,'SymLinkMakeDummyFile',default=True))
            else:
                e=env.fs.Entry('.'+os.sep+src.name, dnode)
            tmp=copy_logic(target=e,source=src,**kw)
            n_targets.extend(tmp)
            
            
    return n_targets


def CCopyAsWrapper(env, target=None, source=None,copy_logic=CCopy.default,**kw):
    result = []
    #setup copy function
    if copy_logic == CCopy.default:
        copy_logic=env.get('CCOPY_LOGIC',CCopy.copy) # make fallback a safe one
    if copy_logic == CCopy.copy:
        copy_logic=env.__CCopyBuilderC__
    elif copy_logic == CCopy.hard_soft_copy:
        copy_logic=env.__CCopyBuilderHSC__
    elif copy_logic == CCopy.soft_hard_copy:
        copy_logic=env.__CCopyBuilderSHC__
    elif copy_logic == CCopy.hard_copy:
        copy_logic=env.__CCopyBuilderHC__
    elif copy_logic == CCopy.soft_copy:
        copy_logic=env.__CCopyBuilderSC__
    else:
        copy_logic=env.__CCopyBuilderC__
        
    for src, tgt in map(lambda x, y: (x, y), source, target):
        result.extend(copy_logic(tgt, src,**kw))
    return result

    #n_targets=env.__SDKBuilder__(target=target,source=source)
    #return results


def _sdk_copy(env, target=None, source=None,copy_logic=CCopy.default,**kw):
    reporter.report_warning("_SDKCOPY_ is an internal function, please use CCopy")
    return env.CCopy(target, source,copy_logic,**kw)
    

def _sdk_copyas(env, target=None, source=None,copy_logic=CCopy.default,**kw):
    reporter.report_warning("_SDKCOPYAs_ is an internal function, please use CCopyAs")
    return env.CCopyAs(target, source,copy_logic,**kw)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.CCopy=CCopyWrapper
SConsEnvironment.CCopyAs=CCopyAsWrapper

SConsEnvironment._SDKCOPY_=_sdk_copy
SConsEnvironment._SDKCOPYAs_=_sdk_copyas

common.AddBuilder('__CCopyBuilderHSC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            lambda target, source, env: CCopyFunc(target, source, env,ccopy_hard_soft),
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        multi          = 1,
        emitter        = CCopyEmit
        ))

common.AddBuilder('__CCopyBuilderSHC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            lambda target, source, env: CCopyFunc(target, source, env,ccopy_soft_hard),
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        multi          = 1,
        emitter        = CCopyEmit
        ))

common.AddBuilder('__CCopyBuilderHC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            lambda target, source, env: CCopyFunc(target, source, env,ccopy_hard),
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        multi          = 1,
        emitter        = CCopyEmit
        ))
common.AddBuilder('__CCopyBuilderSC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            lambda target, source, env: CCopyFunc(target, source, env,ccopy_soft),
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        multi          = 1,
        emitter        = CCopyEmit
        ))
common.AddBuilder('__CCopyBuilderC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            lambda target, source, env: CCopyFunc(target, source, env,ccopy_copy),
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        multi          = 1,
        emitter        = CCopyEmit
        ))

common.add_global_value('CCopy',CCopy)        
common.add_parts_object('CCopy',CCopy)        
        
        
common.AddEnumVariable('CCOPY_LOGIC','hard-soft-copy','',['hard-soft-copy','soft-hard-copy','hard-copy','soft-copy','copy'])
        
        