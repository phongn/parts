
import os,sys
import re
import SCons.Util

from SCons.Debug import logInstanceCreation

class PathFinder(object):
    '''
    Provides information
    '''
    def __init__(self,paths):
        if __debug__: logInstanceCreation(self)
        self.paths=paths

    def __call__(self):
        ret=None
        for p in self.paths:
            if os.path.isdir(p):
                ret=p
                #print('Found default path [%s]' % (p))
                return ret
            else:
                #print('Did not find default path [%s]' % (p))
                pass
        return ret

class EnvFinder(object):
    def __init__(self,keys,rel_path=None):
        if __debug__: logInstanceCreation(self)
        self.keys=keys
        self.rel_path=rel_path

    def __call__(self):

        for key in self.keys:
            ret = os.environ.get(key, None)
            if ret==None:
                #print('Shell value %s not found' % (key))
                pass
            elif os.path.isdir(ret):
                #print('Found shell value %s with value of %s' % (key,ret))
                pass
            else:
                #print('Path value of %s for varible of %s does not exists' % (ret,key))
                pass
        if self.rel_path != None and ret != None:
            ret = os.path.normpath(os.path.join(ret,self.rel_path))
        return ret

class RegFinder(object):
    def __init__(self,keys,rel_path=None):
        if __debug__: logInstanceCreation(self)
        self.keys=keys
        self.rel_path=rel_path

        if self.keys is None or self.keys == []:
            print "RegFinder was given not passed any values to find"

    def read_reg(self,value):
        ret=SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)
        return ret[0]

    def __call__(self):
        ret=None
        for key in self.keys:
            try:
                ret = self.read_reg(key)
                #print('Found key in registry: %s' % ret)
                break
            except WindowsError, e:
                #print('Did not find key %s in registry' % (ret))
                ret=None
        if self.rel_path != None and ret != None:
            ret = os.path.normpath(os.path.join(ret,self.rel_path))
        return ret

# special windows only finder that looks up data based on how MSI files 
# store information in the registry hive. On non windows system this is
# an empty object that does nothing
if sys.platform == 'win32':
    import parts.platformspecific.win32.msi as msi
    class MsiFinder(object):
        def __init__(self,match_pattern,match_key,installroot_key='InstallLocation'):
            self.match_pattern=match_pattern
            self.match_key=match_key
            self.installroot_key=installroot_key

        def __call__(self):
            for product in msi.allProducts():
                if hasattr(product,self.installroot_key) and\
                    hasattr(product,self.match_key) and\
                    re.match(self.match_pattern, getattr(product,self.match_key,"")):
                        #return None if there is an issue getting the key 
                        return getattr(product,self.installroot_key)
            # nothing was found
            return None
else:
    class MsiFinder(object):
        def __init__(self,*lst,**kw):
            pass
        def __call__(self):
            return None

class ScriptFinder(object):
    def __init__(self,name,args=None):
        if __debug__: logInstanceCreation(self)
        self.name=name
        self.args=args

    def __call__(self,env):
        #get the full path
        p=env.subst(self.name)
        p=os.path.normpath(p)
        if os.path.isfile(p):
            return p
        return None


