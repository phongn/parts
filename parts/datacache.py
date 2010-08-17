import cPickle
import os
import reporter
import common
import SCons.Script

__cache={}
__dirty_cache=[]

def load_cache_data(datafile):
    try:
        if os.path.exists(datafile):
            output = open(datafile, 'rb')
            tmp=cPickle.load(output)
            (tmp,stored_data)=tmp
            output.close()
            return (tmp,stored_data)
    except IOError,ec:
        pass
    except Exception,ec:
        reporter.report_warning("Failed to load datacache file %s, will rebuild file."%datafile)
    return None

def store_cache_data(datafile,data):
    print "storing data file",datafile
    path,filename=os.path.split(datafile)
    if not os.path.exists(path):
        os.makedirs(path)
    output = open(datafile, 'wb')
    cPickle.dump(("some csig",data), output)
    output.close()
    

def GetCache(name,key=None):
    '''
    get data from data cache.. if in memory use that, else load it.
    '''
    global __cache
    if SCons.Script.GetOption("parts_cache") == False:
        return None
    #if key is None get default key
    key=_get_default_key()
    filename=os.path.join(".parts.cache",key,name+".cache")
    # see if we have it already loaded
    try:
        return __cache[filename]
    except KeyError:
        # if not already loaded we load it
        ret=load_cache_data(filename)
        if ret is not None:
            __cache[filename]=ret[1]
            return ret[1]
    # we don't have a cache for this combo
    
    return None

def StoreData(name,data,key=None):
    '''
    set the value of this cache and save the data
    '''
    global __cache
    #if key is None get default key
    key=_get_default_key()
    filename=os.path.join(".parts.cache",key,name+".cache")
    __cache[filename]=data
    __dirty_cache.append(filename)
    #store_cache_data(filename,data)

def SaveCache(name=None,key=None):
    '''
    this will save the data of all caches is Name is None
    else it will save on the data of a given item, it it exists
    '''
    global __cache,__dirty_cache
    if name is None and key is not None:
        print "error"
    elif name is None:
        for k in __dirty_cache:
            store_cache_data(k,__cache[k])
        __dirty_cache=[]
        
    else:
        #if key is None get default key
        key=_get_default_key()
        filename=os.path.join(".parts.cache",key,name+".cache")
        try:
            if filename in __dirty_cache:
                data=__cache[filename]
                store_cache_data(filename,data)
                __dirty_cache.remove(filename)
        except KeyError:
            pass
        
def ClearCache(name=None,key=None):
    '''
    Clear out the cache of data in memory
    '''
    global __cache
    if name is None and key is not None:
        print "error"
    elif name is None:
        del __cache
        __cache={}
    else:
        #if key is None get default key
        key=_get_default_key()
        filename=os.path.join(".parts.cache",key,name+".cache")
        try:
            del __cache[filename]
        except KeyError:
            pass
    
        
def _get_default_key():
    return common.g_engine._cache_key
    
    