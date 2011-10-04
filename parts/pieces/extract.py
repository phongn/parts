import os
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
from parts.common import matches
from parts import api
from parts import datacache
import hashlib

try:
    import cPickle as pickle
except:
    import pickle

class Cache:
    def __init__(self, file_node, includes, excludes):
        self.file_node = file_node
        self.includes = includes
        self.excludes = excludes
        self.fileinfo = {
            'HEADER': "%s%s" % (
                self.file_node.get_dir().get_abspath(),
                str(self.file_node.getmtime())
                ),
            'ITEMS':{"%s%s" % (str(includes), str(excludes)): []}
        }
    @property
    def key(self):
        return self.file_node.get_path() + str(self.includes) + str(self.excludes)

    def getfiles(self, generator, env):
        
        md5=hashlib.md5()
        md5.update(self.key)
        hash_key=md5.hexdigest()
        
        if not self.file_node.changed():
            files = datacache.GetCache(hash_key,key='extract')
        else:
            files = None

        items = []
        for f in generator:
            item = env.arg2nodes(f, MyFileFactory)
            items.append(item)

        if files is None:
            datacache.StoreData(hash_key,items, key='extract')

        return items

def actionUnzip(target,source,env,includes=['*'],excludes=[]):
    z = zipfile.ZipFile(str(source[0]))
    for f in target:
        try:
            os.makedirs(os.path.split(f.abspath)[0])
        except:
            pass
        file(f.abspath, "wb").write(z.read(f.original_name))
    z.close()
    return 0

def strUnzip(target,source,env):
    return ''

def zipGenerator(t, includes, excludes):
    for i in t.infolist():
        if i.filename[-1] != "/" and matches(i.filename, includes, excludes):
            yield i.filename

def emitterUnzip(target,source,env):
    import time
    start = time.time()
    target = []

    includes = env.get('EXTRACT_INCLUDES') or ['*']
    excludes = env.get('EXTRACT_EXCLUDES') or []

    cache = Cache(source[0], includes, excludes)

    f = zipfile.ZipFile(str(source[0]))

    target = cache.getfiles(zipGenerator(f, includes, excludes), env)

    return target, source

def tarLinkGenerator(tarFile, lnk, targetSet):
    res = []
    f = tarFile.getmember(os.path.normpath(os.path.dirname(lnk.name) + '/' + lnk.linkname))
    if f.islnk() or f.issym():
        r, targetSet = tarLinkGenerator(tarFile, f, targetSet)
        res += r
    if not f.name in targetSet:
        targetSet.add(f.name)
        res.append(f.name)
    return res, targetSet

def tarGenerator(t, includes, excludes):
    res = []
    targetSet = set()
    for i in t.getmembers():
        if not i.isdir() and matches(i.name, includes, excludes):
            if i.islnk() or i.issym():
                r, targetSet = tarLinkGenerator(t, i, targetSet)
                res += r
            if not i.name in targetSet:
                targetSet.add(i.name)
                res.append(i.name)
    return res

def emitterUntar(target,source,env):
    target = []

    includes = env.get('EXTRACT_INCLUDES') or ['*']
    excludes = env.get('EXTRACT_EXCLUDES') or []

    cache = Cache(source[0], includes, excludes)

    f = tarfile.open(str(source[0]))

    target = cache.getfiles(tarGenerator(f, includes, excludes), env)

    return target, source

def makelink(z,i,f):
    # Make sure target exists
    p = os.path.join(os.path.dirname(f), i.linkname)
    t = None
    if not os.path.exists(p):
        t = z.getmember(os.path.dirname(i.name) +'/'+i.linkname)
        if t.isreg():
            writeFile(z, t, p)
        elif t.isdir():
            makeDir(z, t, p)
        elif t.islnk() or t.issym():
            makelink(z,t,p)
    if i.issym():
        os.symlink(i.linkname, f)
    else:
        os.link(p, f)
    if t is not None:
        os.chmod(p, stat.S_IMODE(t.mode))

def writeFile(z, i, f):
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
        try:
            os.makedirs(os.path.dirname(f.abspath))
        except:
            pass
        i = z.getmember(f.original_name)
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
    res.original_name = name
    return res

#def createExtractBuilder(env):
#    try:
#        extract = env['BUILDERS']['Extract']
#    except KeyError:
#        extract = SCons.Builder.Builder(action = {
#                '.zip':env.Action(actionUnzip, strfunction=strUnzip),
#                '.gz':env.Action(actionUntar, strfunction=strUnzip)
#                },
#                                        emitter = {
#                                        '.zip':emitterUnzip,
#                                        '.gz':emitterUntar
#                                        },
#                                        prefix = '',
#                                        suffix = '',
#                                        src_suffix = ['.zip', '.gz'],
#                                        target_factory = MyFileFactory)
#        env['BUILDERS']['Extract'] = extract
#
#    return extract
#
api.register.add_builder('Extract',
        SCons.Builder.Builder(
            action = {
                '.zip': SCons.Action.Action(actionUnzip, strfunction = strUnzip),
                '.gz' : SCons.Action.Action(actionUntar, strfunction = strUnzip)
            },
            emitter = {
                '.zip': emitterUnzip,
                '.gz' : emitterUntar
            },
            prefix = '',
            suffic = '',
            src_suffix = ['.zip', '.gz'],
            target_factory = MyFileFactory)
        )

# vim: set et ts=4 ai :
