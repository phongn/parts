import os
import sys
import zipfile
import tarfile
import SCons.Builder
import SCons.Action
import SCons.Util
import SCons.Node.FS
import SCons.Environment
import time
import shutil
import stat
import ctypes
from parts.common import matches
from parts import api
from parts import datacache

class SymlinkException(BaseException):
    pass

try:
    symlink = os.symlink
except AttributeError:
    try:
        CreateSymbolicLinkW = ctypes.windll.kernel32.CreateSymbolicLinkW
        symlink = lambda src, dst: CreateSymbolicLinkW(unicode(dst), unicode(src), 1 if os.path.isdir(dst) else 0)
    except AttributeError:
        # it's pity but Windows prior Vista does not have CreateSymbolicLinkW function
        def symlink(src, dst):
            raise SymlinkException("Don't know how to make symlink on Windows XP")

class HardlinkException(BaseException):
    pass

try:
    link = os.link
except AttributeError:
    try:
        CreateHardLinkW = ctypes.windll.kernel32.CreateHardLinkW
        link = lambda src, dst: CreateHardLinkW(unicode(src), unicode(dst), None)
    except AttributeError:
        def link(src, dst):
            raise HardlinkException("Don't know how to make hard link on Windows NT")

def getNodesFromCache(fileNode, generator, env, factory):
    fileNodeCacheName = fileNode.for_signature()
    fileNodeSignature = fileNode.get_csig();
    signature = datacache.GetCache(fileNodeCacheName, key = 'extract')
    if signature != fileNodeSignature:
        datacache.StoreData(fileNodeCacheName, fileNodeSignature, key = 'extract')
        datacache.SaveCache(fileNodeCacheName, key = 'extract')
        nodeNames = [f for f in generator(fileNode)]
        datacache.StoreData(fileNodeCacheName + fileNodeSignature, nodeNames, key = 'extract')
        datacache.SaveCache(fileNodeCacheName + fileNodeSignature, key = 'extract')
    else:
        nodeNames = datacache.GetCache(fileNodeCacheName + fileNodeSignature, key = 'extract')

    nodes = []
    includes = env.get('EXTRACT_INCLUDES', ['*'])
    excludes = env.get('EXTRACT_EXCLUDES', [])
    for nodeName in nodeNames:
        if matches(nodeName, includes, excludes):
            nodes.append(nodeName)

    return env.arg2nodes(nodes, factory)

def actionUnzip(target,source,env):
    z = zipfile.ZipFile(str(source[0]))
    for f in target:
        try:
            os.makedirs(os.path.split(f.abspath)[0])
        except:
            pass
        file(f.abspath, "wb").write(z.read(f.attributes.original_name))
    z.close()
    return 0

def zipGenerator(source):
    res = []
    t = zipfile.ZipFile(str(source))
    for i in t.infolist():
        if i.filename[-1] != "/":
            res.append(i.filename)
    return res

def emitterUnzip(target,source,env):
    target = getNodesFromCache(source[0], zipGenerator, env, MyFileFactory)

    return target, source

##def tarLinkGenerator(tarFile, lnk, targetSet):
##    res = []
##    f = tarFile.getmember(os.path.normpath(os.path.dirname(lnk.name) + '/' + lnk.linkname))
##    if f.islnk() or f.issym():
##        r, targetSet = tarLinkGenerator(tarFile, f, targetSet)
##        res += r
##    if not f.name in targetSet:
##        targetSet.add(f.name)
##        res.append(f.name)
##    return res, targetSet
##
def tarGenerator(source):
    t = tarfile.open(str(source))
    res = []
    targetSet = set()
    for i in t.getmembers():
        if not i.isdir():
            res.append(i.name)
    return res

def emitterUntar(target,source,env):
    target = getNodesFromCache(source[0], tarGenerator, env, MyFileFactory)

    return target, source

if os.sep == '/':
    normArchivePath = os.path.normpath
else:
    # Archives use "/" as separator. Even on Windows
    normArchivePath = lambda x: os.path.normpath(x).replace('\\', '/')

def makelink(z,i,f):
    try:
        os.makedirs(os.path.dirname(f))
    except:
        pass

    # Make sure target exists
    p = os.path.join(os.path.dirname(f), i.linkname)
    t = None
    if not os.path.exists(p):
        t = z.getmember(normArchivePath(os.path.dirname(i.name) +'/'+i.linkname))
        if t.isreg():
            writeFile(z, t, p)
        elif t.isdir():
            makeDir(z, t, p)
        elif t.islnk() or t.issym():
            makelink(z,t,p)
    if i.issym():
        symlink(i.linkname, f)
    else:
        os.link(p, f)
    if t is not None:
        os.chmod(p, stat.S_IMODE(t.mode))

def writeFile(z, i, f):
    try:
        os.makedirs(os.path.dirname(f))
    except:
        pass

    fsrc = None
    fdst = None
    try:
        fdst = file(f, "wb")
        fsrc = z.extractfile(i.name)
        shutil.copyfileobj(fsrc, fdst)
    finally:
        if fdst:
            fdst.close()
        if fsrc:
            fsrc.close()
    os.chmod(f, stat.S_IMODE(i.mode))

def makeDir(z, i, f):
    try:
        os.makedirs(f)
    except:
        pass
    os.chmod(f, stat.S_IMODE(i.mode))

def actionUntar(target,source,env):
    z = tarfile.open(str(source[0]))
    for f in target:
        i = z.getmember(f.attributes.original_name)
        if i.isreg():
            writeFile(z, i, f.abspath)
        elif i.islnk() or i.issym():
            makelink(z, i, f.abspath)
        elif i.isdir():
            makeDir(z, i, f.abspath)
    z.close()
    return 0

def MyFileFactory(name, directory = None, create = 1):
    res = SCons.Node.FS.get_default_fs()._lookup(name, directory, SCons.Node.FS.File, create)
    res.attributes.original_name = name
    return res

api.register.add_builder('Extract',
        SCons.Builder.Builder(
            action = {
                '.zip': SCons.Action.Action(actionUnzip, cmdstr = "Extracting from $SOURCE"),
                '.gz' : SCons.Action.Action(actionUntar, cmdstr = "Extracting from $SOURCE"),
                '.bz2': SCons.Action.Action(actionUntar, cmdstr = "Extracting from $SOURCE")
            },
            emitter = {
                '.zip': emitterUnzip,
                '.gz' : emitterUntar,
                '.bz2': emitterUntar
            },
            prefix = '',
            suffic = '',
            src_suffix = ['.zip', '.gz'],
            target_factory = MyFileFactory)
        )

# vim: set et ts=4 ai :
