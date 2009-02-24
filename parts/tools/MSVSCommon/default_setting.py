import SCons.Script
import common,rootpath

'''
Notes on defaults for the different versions

vc 6 This version has 32-bit compiler
vc2002 (7) This version has 32-bit compiler
vc2003 (7.1) This version has 32-bit compiler
vc2005 (8.0) This version has 32-bit and 64-bit compilers
vc2008 (9.0) This version has 32-bit and 64-bit compilers

EXPRESS

vc2005 - This version will install in the same location as the std version. the main difference is that
the platform SDK is not installed. This means that it has to be setup independently. Does not contain 64-bit compilers

vc2008 - basically the same as professional. Need to check different Reg key to see if it is installed. 
However it will install in same default location as the std versions. Platform SDK is installed in seperate 
location. In this case the SDK will install in program file even on 64-bit systems ( different for what VS will do)
The current version it will use is version 6.0A. The script will use a key 
HKCU\SOFTWARE\Microsoft\Microsoft SDKs\Windows\CurrentInstallFolder
This is true for even 64-bit system ( ie not the WOW6432Node, however there seems to be a copy here as well)
Does not contain 64-bit compilers

'''


PATH_cache={}

def GetMSVCPath(version=None,arch=None):
    '''
    Get the PATH for a given version and architectrue.
    If None is used for version it get all known defaults
    If None is used for Arch then it tries to get the current arch of the OS being used
    It assumes the above functions checked for error, or don't care if empty strings are returned.
    '''
    ret=''
    _arch=arch
    if (version,arch) in PATH_cache.keys():
        return PATH_cache[(version,arch)]
    
    if arch==None:
        arch=common.ChipArchitecture()
    if arch != 'x86' and arch != 'x86_64':
        raise ValueError("Invalid architecture %s, only 'x86' or 'x86_64' is supported" % arch)
     
    if version == None:
        for v in common.SUPPORTED_VERSIONSSTR:
            dict={
            'VCINSTALL':rootpath.msvc_root_dir(v),
            'VSINSTALL':rootpath.msvs_root_dir(v),
            'FRAMEWORK_ROOT':rootpath.framework_root(),
            'FRAMEWORK_ROOT64':rootpath.framework_root64()
            }
            ret+=_subst_(get_path(version,arch),dict)
    else:
        if version not in common.SUPPORTED_VERSIONSSTR:
            raise ValueError("Invalid version %s, only versions of %s are supported" % (version,common.SUPPORTED_VERSIONSSTR))
        dict={
            'VCINSTALL':rootpath.msvc_root_dir(version),
            'VSINSTALL':rootpath.msvs_root_dir(version),
            'FRAMEWORK_ROOT':rootpath.framework_root(),
            'FRAMEWORK_ROOT64':rootpath.framework_root64()
            }
        ret+=_subst_(get_path(version,arch),dict)
    
    PATH_cache[(version,_arch)]=ret
    #print ret
    return ret




def get_shell_enviroment(env, ver, arch="x86"):
    '''this function returns the shell environment for a give version and architecture
    '''
    #first we need to get certain varible
    
    env['VCINSTALL']=rootpath.msvc_root_dir(ver)
    env['VSINSTALL']=rootpath.msvs_root_dir(ver)
    env['FRAMEWORK_ROOT']=rootpath.framework_root()
    env['FRAMEWORK_ROOT64']=rootpath.framework_root64()
    
    shellenv={
    'PATH':env.subst(get_path(ver,arch)),
    'INCLUDE':env.subst(get_include(ver,arch)),
    'LIB':env.subst(get_lib(ver,arch)),
    'LIBPATH':env.subst(get_libpath(ver,arch))
    }

    return shellenv

