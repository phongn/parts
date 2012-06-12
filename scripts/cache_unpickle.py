import sys
import os
import cPickle
import base64
import cStringIO

import scons_setup

class CacheFilenames:
    DIR_NAME_CACHE = '.parts.cache'
    FILE_NODEINFO = 'nodeinfo'
    FILE_VCS = 'vcs'
    FILE_GLOBAL_DATA = 'global_data'
    FILE_PART_MAP = 'part_map'
    EXT_CACHE = '.cache'

class NodeinfoKeys:
    KNOWN_PNODES = 'known_pnodes'
    KNOWN_NODES = 'known_nodes'
    ALIASES = 'aliases'

# Returns tuple (cacheRootDir, cacheDirName, cacheKey, cacheFileName)
# E.g. if cacheFilePath is "zip_package1/.parts.cache/a3e124cd59bd929fed1f43ec55421e66/nodeinfo.cache"
# then returns ("zip_package1", ".parts.cache", "a3e124cd59bd929fed1f43ec55421e66", "nodeinfo")
def split(cacheFilePath):
    (cacheFileDir, cacheFile) = os.path.split(os.path.abspath(cacheFilePath))
    (cacheFilesDir, cacheKey) = os.path.split(cacheFileDir)
    (cacheRootDir, cacheDirName) = os.path.split(cacheFilesDir)
    (cacheName, cacheExt) = os.path.splitext(cacheFile)

    if CacheFilenames.DIR_NAME_CACHE != cacheDirName:
        sys.stderr.write('WARNING: Cache directory name is "%s", expected "%s"' % \
            (cacheDirName, CacheFilenames.DIR_NAME_CACHE))
    if CacheFilenames.EXT_CACHE != cacheExt:
        sys.stderr.write('WARNING: Cache file extension is "%s", expected "%s"' % \
            (cacheExt, CacheFilenames.EXT_CACHE))

    return (cacheRootDir, cacheDirName, cacheKey, cacheName)

def unpickle(cacheFilePath):
    scons_setup.setupDefault()

    (cacheRootDir, cacheDirName, cacheKey, cacheFileName) = split(cacheFilePath)

    import parts.pickle_helpers as pickle_helpers
    import parts.datacache as datacache
    import parts.glb as glb

    # Workaround to let Parts find cache file even if this script is not called
    # from directory where '.parts.cache' directory resides
    load_cache_data_orig = datacache.load_cache_data
    def load_cache_data_wrapper(datafile):
        if not os.path.exists(datafile) and datafile.startswith(cacheDirName):
            datafile = os.path.join(cacheRootDir, datafile)
        assert(os.path.exists(datafile))
        return load_cache_data_orig(datafile)
    datacache.load_cache_data = load_cache_data_wrapper

    glb.engine._cache_key = cacheKey

    output = open(cacheFilePath, 'rb')

    p = cPickle.Unpickler(output)
    p.persistent_load = pickle_helpers.persistent_unpickle
    ((dbKey, dbVersion), storedData) = p.load()

    if isinstance(storedData, dict):
        for rootKey, rootVal in storedData.iteritems():
            if isinstance(rootVal, dict):
                for k, v in rootVal.iteritems():
                    if CacheFilenames.FILE_NODEINFO == cacheFileName and rootKey in \
                            [NodeinfoKeys.KNOWN_NODES, NodeinfoKeys.KNOWN_PNODES]:
                        # This cache file section has complicated/encoded data structure so handle it
                        # in a special way
                        buffin = cStringIO.StringIO(base64.b64decode(v['pinfo']))
                        upkl = cPickle.Unpickler(buffin)
                        upkl.persistent_load = pickle_helpers.persistent_unpickle
                        rootVal[k] = upkl.load()
    else:
        # Hmmm, something unexpected.
        raise Exception('Unexpected cache contents: {0}'.format(storedData))

    output.close()

    return storedData
