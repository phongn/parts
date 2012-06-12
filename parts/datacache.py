import glb
import common
import api.output
import pickle_helpers
import errors

import cPickle
import os
import fnmatch

import SCons.Script

__cache={}
__dirty_cache=[]
__db_key={}
__bad_cache=False

def db_key(length):
    global __db_key
    try:
        return __db_key[length]
    except KeyError:
        import hashlib
        md5=hashlib.md5()
        md5.update("DB Cache Version 1.1 length %s"%(length))
        __db_key[length]=md5.hexdigest()
    return __db_key[length]
     


def load_cache_data(datafile):
    #return None
    #if os.path.exists(datafile):
    #        output = open(datafile, 'rb')
    #        p= cPickle.Unpickler(output)
    #        p.persistent_load =pickle_helpers.persistent_unpickle
    #        tmp=p.load()
    #        (tmp,stored_data)=tmp
    #        output.close()
    #        return (tmp,stored_data)
    try:
        if os.path.exists(datafile):
            output = open(datafile, 'rb')
            p= cPickle.Unpickler(output)
            p.persistent_load =pickle_helpers.persistent_unpickle
            tmp=p.load()
            (tmp,stored_data)=tmp
            output.close()
            return (tmp,stored_data)
    except IOError,ec:
        pass
    except Exception,ec:
        api.output.warning_msg("Failed to load datacache file %s, will rebuild file."%datafile,print_once=True)
        global __bad_cache
        __bad_cache=True
        
    return None

def store_cache_data(datafile,data):
    #print "storing data file",datafile
    path,filename=os.path.split(datafile)
    if not os.path.exists(path):
        os.makedirs(path)
    output = open(datafile, 'wb')
    try:
        v=data.get('__version__',0)
    except AttributeError:
        v=0
    p= cPickle.Pickler(output)
    p.persistent_id=pickle_helpers.persistent_pickle
    try:
        p.dump(((db_key(len(data)),v),data))
    except TypeError:
        p.dump(((db_key(1),v),data))
    output.close()
    

__use_parts_cache = None
def GetCache(name,key=None):
    '''
    get data from data cache.. if in memory use that, else load it.
    '''
    global __cache
    global __use_parts_cache

    # Performance note
    # Using 'if SCons.Script.GetOption('parts_cache') == False ...' is the first thing you want to use
    # but it called tooooo many times that's why we cache its returned value.
    if __use_parts_cache is None:
        __use_parts_cache = SCons.Script.GetOption('parts_cache') or False
    if __use_parts_cache == False or __bad_cache==True:
        return None
    #if key is None get default key
    if key is None:
        key=_get_default_key()

    # Performance note
    # str.join method is 20 times faster than os.path.join function
    # and it is safe to call it here because neither key nor name contain os.sep
    filename=os.sep.join([".parts.cache",key,name+".cache"])
    # see if we have it already loaded
    try:
        return __cache[filename]
    except KeyError:
        # if not already loaded we load it
        ret=load_cache_data(filename)
        if ret is not None:
            try:
                v=ret[1].get('__version__',0)
            except AttributeError:
                v=0
            try:
                if ret[0] == (db_key(len(ret[1])),v):
                    __cache[filename]=ret[1]
                    return ret[1]
            except TypeError:
                if ret[0] == (db_key(1),v):
                    __cache[filename]=ret[1]
                    return ret[1]
    # we don't have a cache for this combo
    __cache[filename]=None
    return None

def StoreData(name,data,key=None):
    '''
    set the value of this cache and save the data
    '''
    global __cache
    if key is None: #get default key
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
    
    # store everything for a given key
    if name is None and key:
        tmp=os.path.join(".parts.cache",key,"*.cache")
        for k in __dirty_cache[:]:
            #see if the path matched
            if fnmatch.fnmatchcase(k, tmp):
                store_cache_data(k,__cache[k])
                __dirty_cache.remove(k)
                
    # store everything case
    elif name is None and key is None:
        for k in __dirty_cache:
            store_cache_data(k,__cache[k])
        __dirty_cache=[]
    
    # store everything for a given name and default key
    elif name and key is None:
        key=_get_default_key()
        filename=os.path.join(".parts.cache",key,name+".cache")
        
        if filename in __dirty_cache:
            data=__cache[filename]
            store_cache_data(filename,data)
            __dirty_cache.remove(filename)
        
    
    # store a give name for a given key
    else:
        filename=os.path.join(".parts.cache",key,name+".cache")

        if filename in __dirty_cache:
            data=__cache[filename]
            store_cache_data(filename,data)
            __dirty_cache.remove(filename)
        
def ClearCache(name=None,key=None,save=False):
    '''
    Clear out the cache of data in memory
    '''
    global __cache,__dirty_cache
    
    def clear_item(item):
        try:
            del __cache[item]
            __dirty_cache.remove(item)
        except KeyError:
            pass
        except ValueError:
            pass
    
    if save:
        SaveCache(name,key)
     # clear everything for a given key
    if name is None and key:
        tmp=os.path.join(".parts.cache",key,"*.cache")
        for k in __cache.keys():
            #see if the path matched
            if fnmatch.fnmatchcase(k, tmp):
                clear_item(k)
                
    # clear everything case
    elif name is None and key is None:
        del __cache
        __cache={}
        del __dirty_cache
        __dirty_cache=[]
    # clear everything for a given name and default key
    elif name and key is None:
        key=_get_default_key()
        filename=os.path.join(".parts.cache",key,name+".cache")
        clear_item(filename)
    
    # clear a give name for a given key
    else:
        filename=os.path.join(".parts.cache",key,name+".cache")
        clear_item(filename)

    
        
def _get_default_key():
    return glb.engine._cache_key
    
    
