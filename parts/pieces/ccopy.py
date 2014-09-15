
import SCons.Script
import sys
import os
import shutil
import parts.common as common
import parts.api as api
import parts.overrides.symlinks as symlinks
import parts.api.output as output
import stat
import errno
from parts.part_logger import part_nil_logger

from collections import deque

# generic copy builder
if sys.platform == 'win32':
    import ctypes
    from ctypes.wintypes import BOOLEAN, LPWSTR, DWORD

    # this function is return value is messed up because of a programmer mistake as MS
    # have to reprototype it do it works correctly. basically make return a BOOLEAN not a BOOL
    try:
        CreateSymbolicLink = ctypes.windll.kernel32.CreateSymbolicLinkW
        CreateSymbolicLink.argtypes = (
            ctypes.wintypes.LPWSTR,
            ctypes.wintypes.LPWSTR,
            ctypes.wintypes.DWORD,
            )
        CreateSymbolicLink.restype = ctypes.wintypes.BOOLEAN
    except AttributeError: # CreateSymbolicW not found
        def CreateSymbolicLink(arg1, arg2, arg3):
            ctypes.SetLastError(1) #ERROR_INVALID_FUNCTION
            return 0

    def ccopy_hard_soft(dest,source):
        # we only deal with files in our cases
        api.output.verbose_msgf("ccopy","ccopy_hard_soft dest={0} source={1}",dest,source)
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
        try:

            ret=ctypes.windll.kernel32.CreateHardLinkW(unicode(dest),unicode(source),0)
            if ret==0:
                api.output.verbose_msgf("ccopy","Failed to create HardLink: {0}",ctypes.FormatError(ctypes.GetLastError()))
                raise IOError,ctypes.FormatError(ctypes.GetLastError())
        except:
            try:
                #get the relpath
                tmp=os.path.split(source)
                tmp=os.path.join(common.relpath(tmp[0],os.path.split(dest)[0]),tmp[1])
                ret=CreateSymbolicLink(unicode(dest),unicode(tmp),0)
                if ret==0:
                    api.output.verbose_msgf("ccopy","Failed to create Symlink: {0}",ctypes.FormatError(ctypes.GetLastError()))
                    raise IOError,ctypes.FormatError(ctypes.GetLastError())
            except:
                ret=ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
                if ret==0:
                    api.output.verbose_msgf("ccopy","Failed to copy: {0}",ctypes.FormatError(ctypes.GetLastError()))
                    raise ctypes.WinError()

    def ccopy_soft_hard(dest,source):
        # we only deal with files in our cases
        api.output.verbose_msgf("ccopy","ccopy_soft_hard dest={0} source={1}",dest,source)
        #get the relpath
        tmp=os.path.split(source)
        tmp=os.path.join(common.relpath(tmp[0],os.path.split(dest)[0]),tmp[1])
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
        try:
            ret=CreateSymbolicLink(unicode(dest),unicode(tmp),0)
            if ret==0:
                api.output.verbose_msgf("ccopy","Failed to create Symlink: {0}",ctypes.FormatError(ctypes.GetLastError()))
                raise IOError,ctypes.FormatError(ctypes.GetLastError())
        except:
            try:
                ret=ctypes.windll.kernel32.CreateHardLinkW(unicode(dest),unicode(source),0)
                if ret==0:
                    api.output.verbose_msgf("ccopy","Failed to create HardLink: {0}",ctypes.FormatError(ctypes.GetLastError()))
                    raise IOError,ctypes.FormatError(ctypes.GetLastError())
            except:
                ret=ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
                if ret==0:
                    api.output.verbose_msgf("ccopy","Failed to copy: {0}",ctypes.FormatError(ctypes.GetLastError()))
                    raise ctypes.WinError()

    def ccopy_hard(dest,source):
        # we only deal with files in our cases
        api.output.verbose_msgf("ccopy","ccopy_hard dest={0} source={1}",dest,source)
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
        try:
            ret=ctypes.windll.kernel32.CreateHardLinkW(unicode(dest),unicode(source),0)
            if ret==0:
                api.output.verbose_msgf("ccopy","Failed to create HardLink: {0}",ctypes.FormatError(ctypes.GetLastError()))
                raise IOError,ctypes.FormatError(ctypes.GetLastError())
        except:
            ret=ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
            if ret==0:
                api.output.verbose_msgf("ccopy","Failed to copy: {0}",ctypes.FormatError(ctypes.GetLastError()))
                raise ctypes.WinError()

    def ccopy_soft(dest,source):
        # we only deal with files in our cases
        #get the relpath
        api.output.verbose_msgf("ccopy","ccopy_soft dest={0} source={1}",dest,source)
        tmp=os.path.split(source)
        tmp=os.path.join(common.relpath(tmp[0],os.path.split(dest)[0]),tmp[1])
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
        try:
            ret=CreateSymbolicLink(unicode(dest),unicode(tmp),0)
            if ret==0:
                api.output.verbose_msgf("ccopy","Failed to create Symlink: {0}",ctypes.FormatError(ctypes.GetLastError()))
                raise IOError,ctypes.FormatError(ctypes.GetLastError())
        except:
            ret=ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
            if ret==0:
                api.output.verbose_msgf("ccopy","Failed to copy: {0}",ctypes.FormatError(ctypes.GetLastError()))
                raise ctypes.WinError()

    def ccopy_copy(dest,source):
        api.output.verbose_msgf("ccopy","ccopy_copy dest={0} source={1}",dest,source)
        ret=ctypes.windll.kernel32.CopyFileW(unicode(source),unicode(dest),False)
        if ret==0:
            api.output.verbose_msgf("ccopy","Failed to copy: {0}",ctypes.FormatError(ctypes.GetLastError()))
            raise ctypes.WinError()
else:
    def ccopy_hard_soft(dest,source):
        api.output.verbose_msgf("ccopy","ccopy_hard_soft dest={0} source={1}",(dest,source))
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
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
        api.output.verbose_msgf("ccopy","ccopy_soft_hard dest={0} source={1}",dest,source)
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
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
        api.output.verbose_msgf("ccopy","ccopy_hard dest={0} source={1}",dest,source)
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
        try:
            os.link(source,dest)
        except:
            shutil.copy2(source, dest)
            st = os.stat(source)
            os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    def ccopy_soft(dest,source):
        api.output.verbose_msgf("ccopy","ccopy_soft dest={0} source={1}",dest,source)
        if os.path.exists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} exists on disk, deleting file so links can be created correctly',dest)
            os.remove(dest)
        try:
            os.symlink(source,dest)
        except:
            shutil.copy2(source, dest)
            st = os.stat(source)
            os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)

    def ccopy_copy(dest,source):
        api.output.verbose_msgf("ccopy","ccopy_copy dest={0} source={1}",dest,source)
        if os.path.lexists(dest):
            api.output.verbose_msgf("ccopy",'File: {0} links exists on disk, deleting file so copy can be created correctly',dest)
            os.remove(dest)
        shutil.copy2(source, dest)
        st = os.stat(source)
        os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)


def on_rmtree_error(function, path, exc_info):
    if function == os.remove:
        os.chmod(os.lstat(path).st_mode | 0o222)
        os.remove(path)

try:
    WindowsError
except NameError:
    WindowsError = None

def copytree(src, dst):
    '''
    We use our version of copytree because one from shutil fails when destination
    directory exists already.
    '''
    dirs = deque(['.'])
    while dirs:
        current = dirs.popleft()
        src_dir = os.sep.join((src, current))
        dst_dir = os.sep.join((dst, current))

        # Make sure the destination directory exists
        try:
            os.makedirs(dst_dir)
        except OSError, error:
            if error.errno == errno.EEXIST:
                if not os.path.isdir(dst_dir):
                    raise SCons.Errors.UserError, ("cannot overwrite non-directory "
                            "'%s' with a directory '%s'") % (dst_dir, src_dir)
            else:
                raise

        # Iterate by source directory entries.
        # Files are copied, directories are add to the dirs list.
        for entry in os.listdir(src_dir):
            src_entry = os.sep.join((src_dir, entry))
            if os.path.isdir(src_entry):
                dirs.append(os.sep.join((current, entry)))
            else:
                shutil.copy2(src_entry, os.sep.join((dst_dir, entry)))

        try:
            shutil.copystat(src, dst)
        except OSError, why:
            if WindowsError is not None and isinstance(why, WindowsError):
                # Copying file access times may fail on Windows
                pass
            else:
                raise

def CCopyFuncWrapper(env, dest, source, copyfunc):

    if os.path.isdir(source):
        copytree(source, dest)
    else:
        copyfunc(dest,source)

    return 0

def CCopyFunc(target, source, env, copy_logic):

    # get the logger for the given part
    output=env._get_part_log_mapper()
    # tell it we are starting a task
    id=output.TaskStart(CCopyStringFunc(target,source,env)+"\n")

    assert( len(target) == len(source) ), "\ntarget: %s\nsource: %s" %(map(str, target),map(str, source))

    for t, s in zip(target, source):
        #Get info if this should be handled as a symlink
        if isinstance(s, symlinks.FileSymbolicLink):
            assert s.exists() and s.linkto
            # A symbolic link can only be a copy of another symlink.
            # Convert a target node to FileSymbolicLink this is needed for 
            # correct up-to-date checks during incremental builds
            symlinks.ensure_node_is_symlink(t)
            if t.linkto is None:
                t.linkto = s.linkto
            symlinks.make_link_bf([t], [t.Entry(t.linkto)], env)
        else:
            #Do normal copy stuff
            env.CCopyFuncWrapper(t.get_path(), s.get_path(), copy_logic)
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
    target, source = target[0], source[0]
    target.must_be_same(type(source))
    return [target], [source]


class CCopy(object):
    default=0
    copy=1
    hard_soft_copy=2
    soft_hard_copy=3
    hard_copy=4
    soft_copy=5

def convert(str):
    if common.is_string(str):
        if str=='hard-soft-copy':
            return CCopy.hard_soft_copy
        elif str=='soft-hard-copy':
            return CCopy.soft_hard_copy
        elif str=='hard-copy':
            return CCopy.hard_copy
        elif str=='soft-copy':
            return CCopy.soft_copy
        elif str=='copy':
            return CCopy.copy
        else:
            api.output.warning_msg("unknown string value for CCOPY_LOGIC")
    return str



def CCopyWrapper(env, target=None, source=None,copy_logic=CCopy.default,**kw):

    target_factory = env.fs
    # test args a little
    try:
        dnodes = env.arg2nodes(target, target_factory.Dir)
    except TypeError:
        exc_typ, value, trace_back = sys.exc_info()
        # now try to get the bad guy by going to the end:
        try:
            while trace_back.tb_next:
                trace_back = trace_back.tb_next

            try:
                bad_value = str(trace_back.tb_frame.f_locals['self'])
            except KeyError:
                bad_value = 'Unknown'
            api.output.error_msg("Target `%s' is a file, but should be a directory.  Perhaps you have the arguments backwards?" % str(bad_value))
        finally:
            del trace_back


    #setup copy function
    copy_logic_bak = copy_logic
    if copy_logic == CCopy.default:
        copy_logic=convert(
            env.get('CCOPY_LOGIC',CCopy.copy) # make fallback a safe one
            )

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

    sources=common.make_list(source)
    
    n_targets = []
    for dnode in dnodes:
        for src in sources:
            if common.is_string(src):
                src=env.arg2nodes(src, env.fs.Entry)[0]
                # Prepend './' so the lookup doesn't interpret an initial
                # '#' on the file name portion as meaning the Node should
                # be relative to the top-level SConstruct directory.
                e = dnode.Entry(os.sep.join(['.', src.name]))
            elif isinstance(src, SCons.Node.FS.Dir):
                e = dnode.Dir(os.sep.join(['.', src.name]))
            elif isinstance(src, symlinks.FileSymbolicLink):
                #symlinks.ensure_node_is_symlink(e)
                try:
                    e=dnode.FileSymbolicLink(os.sep.join(['.', src.name]))
                except:
                    # this is a hack to deal with some backward compatibility issue
                    # with deal with symlinks in old code
                    e = dnode.Entry(os.sep.join(['.', src.name]))
                    symlinks.ensure_node_is_symlink(e)
            elif isinstance(src, SCons.Node.FS.File):
                e = dnode.File(os.sep.join(['.', src.name]))
            else:
                # should not happen...
                e = dnode.Entry(os.sep.join(['.', src.name]))
        
            tmp=copy_logic(target=e,source=src,**kw)

            try:
                tmp[0].attributes = src.attributes
            except (AttributeError, IndexError):
                pass

            # Let source node know what copies of it are to be created.
            # This information will be used to set up correct symbolic
            # links in the destination directory
            try:
                copiedas = src.attributes.copiedas
            except AttributeError:
                src.attributes.copiedas = copiedas = []
            copiedas.append(e)

            n_targets.extend(tmp)

    return n_targets


def CCopyAsWrapper(env, target=None, source=None,copy_logic=CCopy.default,**kw):
    result = []
    #setup copy function

    if copy_logic == CCopy.default:
        copy_logic=convert(
            env.get('CCOPY_LOGIC',CCopy.copy) # make fallback a safe one
            )

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

    source = env.arg2nodes(source)
    target = env.arg2nodes(target)

    if len(target) <> len(source):
        api.output.error_msg("Number of targets and sources should be the same")

    for src, tgt in zip(source, target):
        #if the tragets is a string and the source is a symlink, we want to make the target a symlink as well
        if common.is_string(tgt) and isinstance(src, symlinks.FileSymbolicLink):
            result.extend(env.SymLink(tgt,src.linkto))
        else:
            result.extend(copy_logic(tgt, src, **kw))
    return result



def _sdk_copy(env, target=None, source=None,copy_logic=CCopy.default,**kw):
    api.output.warning_msg("_SDKCOPY_ is an internal function, please use CCopy")
    return env.CCopy(target, source,copy_logic,**kw)


def _sdk_copyas(env, target=None, source=None,copy_logic=CCopy.default,**kw):
    api.output.warning_msg("_SDKCOPYAs_ is an internal function, please use CCopyAs")
    return env.CCopyAs(target, source,copy_logic,**kw)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.CCopy=CCopyWrapper
SConsEnvironment.CCopyAs=CCopyAsWrapper
SConsEnvironment.CCopyFuncWrapper=CCopyFuncWrapper

SConsEnvironment._SDKCOPY_=_sdk_copy
SConsEnvironment._SDKCOPYAs_=_sdk_copyas

def copy_hard_soft_action(target,source,env):
    return CCopyFunc(target, source, env,ccopy_hard_soft)
def copy_soft_hard_action(target,source,env):
    return CCopyFunc(target, source, env,ccopy_soft_hard)
def copy_hard_action(target,source,env):
    return CCopyFunc(target, source, env,ccopy_hard)
def copy_soft_action(target,source,env):
    return CCopyFunc(target, source, env,ccopy_soft)
def copy_copy_action(target,source,env):
    return CCopyFunc(target, source, env,ccopy_copy)

api.register.add_builder('__CCopyBuilderHSC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            copy_hard_soft_action,
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        #multi          = 1,
        emitter        = CCopyEmit,
        source_scanner = symlinks.source_scanner,
        name='CCOPY'
        ))

api.register.add_builder('__CCopyBuilderSHC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            copy_soft_hard_action,
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        #multi          = 1,
        emitter        = CCopyEmit,
        source_scanner = symlinks.source_scanner,
        name='CCOPY'
        ))

api.register.add_builder('__CCopyBuilderHC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            copy_hard_action,
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        #multi          = 1,
        emitter        = CCopyEmit,
        source_scanner = symlinks.source_scanner,
        name='CCOPY'
        ))
api.register.add_builder('__CCopyBuilderSC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            copy_soft_action,
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        #multi          = 1,
        emitter        = CCopyEmit,
        source_scanner = symlinks.source_scanner,
        name='CCOPY'
        ))
api.register.add_builder('__CCopyBuilderC__',SCons.Builder.Builder(
        action         = SCons.Action.Action(
            copy_copy_action,
            CCopyStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        #multi          = 1,
        emitter        = CCopyEmit,
        source_scanner = symlinks.source_scanner,
        name='CCOPY'
        ))

api.register.add_global_object('CCopy',CCopy)
api.register.add_global_parts_object('CCopy',CCopy)


api.register.add_enum_variable('CCOPY_LOGIC','hard-soft-copy',
        '',['hard-soft-copy','soft-hard-copy','hard-copy','soft-copy','copy'])


