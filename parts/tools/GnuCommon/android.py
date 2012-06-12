
import os
import parts.tools.Common.Finders as Finders
import common

#android scanner for Windows
class win_scanner(object):
    def __init__(self,env,arch,tool_prefix,tool):
        self.arch=arch
        self.env_var=Finders.EnvFinder(env)
        self.tool_prefix=tool_prefix
        self.tool=tool
        self.cache=None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # we will scan for three possible locations
            #being a home directory,program files and c drive
            # we will also look at an environment variable NDK_ROOT
            ndk_root=self.env_var()
            paths=[os.path.expanduser('~'),'C:\Program Files (x86)\Android','C:\Program Files\Android',"c:\\","\\"]
            if ndk_root:
                paths=[ndk_root]+paths

            for path in paths:
                if not os.path.isdir(path):
                    continue
                for item0 in os.listdir(path):
                    if item0.lower().startswith("android-ndk-") or ndk_root == path:
                        if ndk_root == path:
                            ndk_path=ndk_root
                        else:
                            ndk_path=os.path.join(path,item0)
                        temp=os.path.join(ndk_path,'toolchains')
                            
                        # we check to get the version of the compiler
                        # we assume that a given NDK comes with one version of the toolchain
                        # not two versions
                        if os.path.exists(temp) == False:
                            continue
                        version=None
                        archpath=None
                        for item1 in os.listdir(temp):
                            fullpath=os.path.join(temp,item1)
                            if os.path.isdir(fullpath):
                                # if this is a directory
                                if item1.startswith(self.arch):
                                    version=item1.split("-")[-1]
                                    archpath=item1
                                    break
                        # we found a version
                        if version:
                            toolpath=os.path.join(ndk_path,'toolchains',archpath,r'prebuilt\windows\bin',self.tool_prefix+self.tool)
                            if os.path.isfile(toolpath):
                                # we have a hit. store important data
                                ret[version]=ndk_path

            self.cache=ret
        return self.cache

    def resolve_version(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return i
        return None

    def resolve(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return tmp[i]
        return None

#android scanner for posix/mac
class posix_scanner(object):
    def __init__(self,env,arch,tool_prefix,tool):
        self.arch=arch
        self.env_var=Finders.EnvFinder(env)
        self.tool_prefix=tool_prefix
        self.tool=tool
        self.cache=None

    def scan(self):
        # search for all known location for a give version
        if self.cache is None:
            # what we will want to return
            ret={}
            # we will scan for three possible locations
            #being a home directory,program files and c drive
            # we will also look at an environment variable NDK_ROOT
            ndk_root=self.env_var()
            # need to relook at the default paths for posix/mac systems
            paths=[os.path.expanduser('~'),
                   os.path.expanduser('~')+'/Android',
                   os.path.expanduser('~')+'/android',
                   '/opt','/opt/Android',
                   '/opt/android',
                   "/",
                   "/Android",
                   "/android"]
                   
            if ndk_root:
                paths=[ndk_root]+paths

            for path in paths:
                if not os.path.isdir(path):
                    continue
                for item0 in os.listdir(path):
                    if item0.lower().startswith("android-ndk-") or ndk_root == path:
                        if ndk_root == path:
                            ndk_path=ndk_root
                        else:
                            ndk_path=os.path.join(path,item0)
                        temp=os.path.join(ndk_path,'toolchains')
                            
                        # we check to get the version of the compiler
                        # we assume that a given NDK comes with one version of the toolchain
                        # not two versions
                        if os.path.exists(temp) == False:
                            continue
                        version=None
                        archpath=None
                        for item1 in os.listdir(temp):
                            fullpath=os.path.join(temp,item1)
                            if os.path.isdir(fullpath):
                                # if this is a directory
                                if item1.startswith(self.arch):
                                    version=item1.split("-")[-1]
                                    archpath=item1
                                    break
                        # we found a version
                        if version:
                            toolpath=os.path.join(ndk_path,'toolchains',archpath,r'prebuilt/linux-x86/bin',self.tool_prefix+self.tool)
                            if os.path.isfile(toolpath):
                                # we have a hit. store important data
                                ret[version]=ndk_path
            self.cache=ret
        return self.cache

    def resolve_version(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return i
        return None

    def resolve(self,version):
        tmp=self.scan()
        if tmp is None:
            return None
        k=tmp.keys()
        #k.reverse()
        for i in k:
            if common.MatchVersionNumbers(version,i):
                return tmp[i]
        return None