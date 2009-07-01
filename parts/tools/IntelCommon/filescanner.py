import SCons.Util
import sys
import re
import os
import parts.tools.Common.Finders as Finders
import common

# for version 11.x
class file_scanner11:
    def __init__(self,path,pattern,pattern2,arch,env):
        self.path=path
        self.pattern=pattern
        self.pattern2=pattern2
        self.arch=arch
        self.env_var=Finders.EnvFinder(env,arch)
        self.cache=None


    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # pattern to match on
            reg=re.compile(self.pattern, re.I)
            reg2=re.compile(self.pattern2, re.I)
            # interate outer directories for match
            if os.path.exists(self.path):
                for item0 in os.listdir(self.path):
                    fullpath0=os.path.join(self.path,item0)
                    # if this is a directory
                    if os.path.isdir(fullpath0):
                        # if this is a directory
                        result0=reg.match(item0)
                        # iterate the inner directories
                        for item in os.listdir(fullpath0):
                            fullpath=os.path.join(fullpath0,item)
                            if os.path.isdir(fullpath):
                                result=reg2.match(item)
                                if result:
                                    version=".".join([item0,item])
                                    ret[version]=fullpath
            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret
        return self.cache
        
    def resolve(self,version):
        tmp=self.scan()
        k=tmp.keys()
        k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return tmp[i]
        return None
    
class file_scanner9_10:
    def __init__(self,path,pattern,arch,env):
        self.path=path
        self.pattern=pattern
        self.arch=arch
        self.env_var=Finders.EnvFinder(env,arch)
        self.cache=None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # pattern to match on
            reg=re.compile(self.pattern, re.I)
            # interate directorys for match
            if os.path.exists(self.path):
                for item in os.listdir(self.path):
                    fullpath=os.path.join(self.path,item)
                    if os.path.isdir(fullpath):
                        result=reg.match(item)
                        if result:
                            version=".".join(result.groups())
                            ret[version]=fullpath
            if ret =={}:
                # ctest env
                ret = self.env_var()
                if ret is not None:
                    ret[self.ver]=ret
            self.cache=ret
        return self.cache
        
    def resolve(self,ver):
        tmp=self.scan()
        k=tmp.keys()
        k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return tmp[i]
        return None  
        
        
