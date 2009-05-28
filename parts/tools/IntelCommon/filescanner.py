import SCons.Util
import sys
import re
import parts.tools.Common.Finders as Finders


# for version 11.x
class file_scanner11:
    def __init__(self,path,pattern,arch,env,ver):
        self.pattern=pattern
        self.reg_keys=regkeys
        self.arch=arch
        self.env_var=Finders.EnvFinder(env,arch)
        self.cache=None
        self.ver=ver

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # pattern to match on
            reg=re.compile(self.pattern, re.I)
            # interate directorys for match
            for item in os.listdir(path):
                if os.path.isdir(item):
                    result=reg.match(item)
                    if result:
                        version=".".join([self.version,item])
                        path=os.path.join(self.path,item)
                        ret[version]=path
            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret
        return self.cache
        
    def resolve(self,ver):
        tmp=self.scan()
        try:
            ver=tmp.keys()[-1]
        except:
            return None
        return tmp[ver]
    
class file_scanner10:
    def __init__(self,path,pattern,arch,env,ver):
        self.pattern=pattern
        self.reg_keys=regkeys
        self.arch=arch
        self.env_var=Finders.EnvFinder(env,arch)
        self.cache=None
        self.ver=ver

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # pattern to match on
            reg=re.compile(self.pattern, re.I)
            # interate directorys for match
            for item in os.listdir(path):
                if os.path.isdir(item):
                    result=reg.match(item)
                    if result:
                        path=os.path.join(self.path,item)
                        ret[".".join(result.groups())]=path
            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret
        return self.cache
        
    def resolve(self,ver):
        tmp=self.scan()
        try:
            ver=tmp.keys()[-1]
        except:
            return None
        return tmp[ver]    
