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


def get_path(ver,arch):
    return vcbin_arch(ver,arch)+vcbin(ver)+vcpackage(ver)+vs_ide(ver)+common_tools(ver)+\
        common_tools_bin(ver)+frameworks_sdk_bin(ver,arch)
def get_include(ver,arch):
    return atlmfc_include(ver)+crt_include(ver) +platformsdk_include(ver)+framework_include(ver)
def get_lib(ver,arch):
    return atlmfc_lib(ver,arch)+crt_lib(ver,arch)+platformsdk_lib(ver,arch)+frameworks_sdk_lib(ver,arch)
def get_libpath(ver,arch):
    return atlmfc_lib(ver,arch)+platformsdk_lib(ver,arch)+frameworks_sdk_lib(ver,arch)
    
   

def atlmfc_include(ver):
    ret=''
    
    if ver=='6.0' :
        ret='${VCINSTALL}ATL\\INCLUDE'+';'+'${VCINSTALL}MFC\\INCLUDE'+';'
    else:
        ret='${VCINSTALL}ATLMFC\\INCLUDE'+';'
    return ret

def atlmfc_lib(ver,arch):
    ret=''
    if ver=='6.0' and arch=='x86':
        ret='${VCINSTALL}MFC\\LIB'+';'
    elif ver=='7.0' and arch=='x86':
        ret='${VCINSTALL}ATLMFC\\LIB'+';'
    elif ver=='7.1' and arch=='x86':
        ret='${VCINSTALL}ATLMFC\\LIB'+';'
    elif ver=='8.0' and arch=='x86':
        ret='${VCINSTALL}ATLMFC\\LIB'+';'
    elif ver=='8.0' and arch=='x86_64':
        ret='${VCINSTALL}ATLMFC\\LIB\\amd64'+';'
    elif ver=='9.0' and arch=='x86':
        ret='${VCINSTALL}ATLMFC\\LIB'+';'
    elif ver=='9.0' and arch=='x86_64':
        ret='${VCINSTALL}ATLMFC\\LIB\\amd64'+';'

    return ret
    

def crt_include(ver):
    ret='${VCINSTALL}INCLUDE'+';'
    return ret

def crt_lib(ver,arch):
    ret=''
    if ver=='8.0' and arch=='x86_64':
        ret='${VCINSTALL}LIB\\amd64'+';'
    elif ver=='9.0' and arch=='x86_64':
        ret='${VCINSTALL}LIB\\amd64'+';'
    else:
        ret='${VCINSTALL}LIB'+';'
    return ret
    
def platformsdk_include(ver,use_sdk=False):
    ''' this will try to update the platform SDK
    to the best SDK version if one is installed
    and the use_sdk is true
    '''
    ret=''
    
    # get the current SDK root based on a req key
    # need for vc 9.0 and newer
    sdk_root=rootpath.get_current_sdk()
    
    if use_sdk==False:
        # use default values
        if ver== '6.0':
            #For this version it is already in the crt_include()
            ret=''
        elif ver== '7.0':
            ret=''
        elif ver== '7.1':
            ret='${VCINSTALL}PlatformSDK\\include'+';'
        elif ver== '8.0':
            ret='${VCINSTALL}PlatformSDK\\include'+';'
        elif ver== '9.0':
            ret=sdk_root+'include'+';'
    return ret

def platformsdk_lib(ver,arch,use_sdk=False):
    ''' this will try to update the platform SDK
    to the best SDK version if one is installed
    and the use_sdk is true
    '''
    ret=''
    
    # get the current SDK root based on a req key
    # need for vc 9.0 and newer
    sdk_root=rootpath.get_current_sdk()
    
    if use_sdk==False:
        # use default values
        if ver== '6.0' and arch=='x86':
            #For this version it is already in the crt_include()
            ret=''
        elif ver== '7.0'and arch=='x86':
            ret=''
        elif ver== '7.1'and arch=='x86':
            ret='${VCINSTALL}PlatformSDK\\lib'+';'
        elif ver== '8.0'and arch=='x86':
            ret='${VCINSTALL}PlatformSDK\\lib'+';'
        elif ver== '8.0'and arch=='x86_64':
            ret='${VCINSTALL}PlatformSDK\\lib\\amd64'+';'
        elif ver== '9.0'and arch=='x86':
            ret=sdk_root+'lib'+';'
        elif ver== '9.0'and arch=='x86_64':
            ret=sdk_root+'lib\\amd64'+';'
    return ret
    
def framework_include(ver):
    ''' This returns the include path need for the framework SDK
    However this is not needed in newer VC drops'''
    ret=''
    
    if ver == '7.0':
        pass
    elif ver == '7.1':
        ret = '${VSINSTALL}SDK\\v1.1\\bin'+';'
    elif ver == '8.0':
        ret = '${VSINSTALL}SDK\\v2.0\\bin'+';'
    return ret

def frameworks_sdk_lib(ver,arch):
    ret=''
    if ver=='7.0' and arch=='x86':
        ret=''
    elif ver=='7.1' and arch=='x86':
        ret='${VSINSTALL}SDK\\v1.1\\lib'+';'
    elif ver=='8.0' and arch=='x86':
        ret='${VSINSTALL}SDK\\v2.0\\lib'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
    elif ver=='8.0' and arch=='x86_64':
        ret='${VSINSTALL}SDK\\v2.0\\lib\AMD64'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
    elif ver=='9.0' and arch=='x86':
        ret='${FRAMEWORK_ROOT}v3.5'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
    elif ver=='9.0' and arch=='x86_64':
        ret='${FRAMEWORK_ROOT64}v3.5'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
    return ret


def frameworks_sdk_bin(ver,arch):
    ret=''
    if ver=='7.0' and arch=='x86':
        ret=''
    elif ver=='7.1' and arch=='x86':
        ret='${VSINSTALL}SDK\\v1.1\\bin'+';'+'${FRAMEWORK_ROOT}v1.1.4322'+';'
    elif ver=='8.0' and arch=='x86':
        ret='${VSINSTALL}SDK\\v2.0\\bin'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
    elif ver=='8.0' and arch=='x86_64':
        ret='${VSINSTALL}SDK\\v2.0\\bin'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
    elif ver=='9.0' and arch=='x86':
        ret='${FRAMEWORK_ROOT}v3.5'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
    elif ver=='9.0' and arch=='x86_64':
        ret='${FRAMEWORK_ROOT64}v3.5'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
    return ret

def common_tools(ver):
    ret='${VSINSTALL}Common7\\Tools\\bin'+';'
    if ver=='6.0':
        ret='${VSINSTALL}Common\\TOOLS\\'+';'
    return ret

def common_tools_bin(ver):
    ret='${VSINSTALL}Common7\\Tools'+';'
    if ver=='6.0':
        ret='${VSINSTALL}Common\\TOOLS\\WINNT'+';'
    return ret

def vs_ide(ver):
    ret='${VSINSTALL}Common7\\IDE'+';'
    if ver=='6.0':
        ret='${VSINSTALL}Common\\msdev98\\BIN'+';'
    return ret

def vcbin(ver):
    ret='${VCINSTALL}BIN'+';'
    return ret

def vcpackage(ver):
    ret='${VCINSTALL}VCPackages'+';'
    if ver=='6.0':
        ret=''
    return ret

def vcbin_arch(ver,arch):
    ''' 
    returns the arch bin path case or empty string
    currently we only handle the x86_64 case,
    can add the x64 case here if needed
    '''
    ret=''

    if arch == 'x86_64' and common.is_win64():
        # it just easier this was... try native then cross in path
        ret = '${VCINSTALL}BIN\\amd64'+';'+'${VCINSTALL}BIN\\x86_amd64'+';'
    elif arch == 'x86_64' and common.is_win64()==False:
        ret = '${VCINSTALL}BIN\\x86_amd64'+';'
    return ret



def _subst_(value,pmap):

    # make an Env with no tools ( would like better way to do subst.. not sure how)
    env=SCons.Script.Environment(tools=[],**pmap) 
    #print  env.subst(value[0])
    return env.subst(value)



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

