
from common import debug
import common
import SCons.Util

import os

#these keys tell us a given version of the compiler is installed
# they will not let us know that a given compiler architecture is installed
# a list is used as some compiler can be installed in different packages
_VC_HKEY_ROOT = {
'6.0':["Software%sMicrosoft\\VisualStudio\\6.0\\Setup\\Microsoft Visual C++\\ProductDir"],
'7.0':["Software%sMicrosoft\\VisualStudio\\7.0\\Setup\\VC\\ProductDir"],
'7.1':["Software%sMicrosoft\\VisualStudio\\7.1\\Setup\\VC\\ProductDir"],
'8.0':["Software%sMicrosoft\\VisualStudio\\8.0\\Setup\\VC\\ProductDir","Software%sMicrosoft\\VCExpress\\8.0\\Setup\\VS\\ProductDir"],
'9.0':["Software%sMicrosoft\\VisualStudio\\9.0\\Setup\\VC\\ProductDir","Software%sMicrosoft\\VCExpress\\9.0\\Setup\\VS\\ProductDir"]
}

#VS_EXPRESS_ROOT_DEFAULTS = {
#8.0:'%s\\Microsoft Visual Studio Express 8\\',
#9.0:'%s\\Microsoft Visual Studio Express 9.0\\'
#}

VC_ROOT_DEFAULTS = {
'6.0':'%s\\Microsoft Visual Studio\\VC98\\',
'7.0':'%s\\Microsoft Visual Studio .NET\\VC7\\',
'7.1':'%s\\Microsoft Visual Studio 7.1.NET 2003\\VC7\\',
'8.0':'%s\\Microsoft Visual Studio 8\\VC\\',
'9.0':'%s\\Microsoft Visual Studio 9.0\\VC\\'
}

VC_SUB_DIR = {
'6.0':'VC98\\',
'7.0':'VC7\\',
'7.1':'VC7\\',
'8.0':'VC\\',
'9.0':'VC\\'
}

vs_root_cache={}
vc_root_cache={}

def msvc_reg_root(version):
    ''' 
    gets the roots msvc path, based on version
    version is a float from 6.0 or better (up to 9.0 currently)
    returns None if we can find this version in the registry
    '''
    
    # make sure we can read
    if not SCons.Util.can_read_reg:
        debug('SCons cannot read registry')
        return None
    
    # currently VS is a 32-bit app. so on any 64-bit Windows installs
    # we need to modify the path we look for information in the registry
    HKEY_ARCH="\\"
    if common.is_win64():
        HKEY_ARCH="\\Wow6432Node\\"
    vcbase = _VC_HKEY_ROOT[version] 
    comps=''
    for key in vcbase:
        key=key % (HKEY_ARCH)
        try:
            comps = common.read_reg(key)
            debug('Found VC dir in registry: %s' % comps)
            break
        except WindowsError, e:
            debug('Did not find VC dir key %s in registry' % \
                  (comps))
            comps=None
        
    if ('6.0' == version) and comps!=None:
        comps+='\\'
    return comps


def msvc_env_root(version):
    '''
    Get the version information via reading the VSXXCOMNTOOLS variable
    Where XX is the a value like 70,80,90
    
    note that vc 6.0 does not support this, in this case this always fails
    '''
    key = common.VSCOMNTOOL_VARNAME[version]
    d = os.environ.get(key, None)

    pdir = None
    if d and os.path.isdir(d):
        debug('%s found from %s' % (d, key))
        pdir=d[:-14]+VC_SUB_DIR[version] 
        
    return pdir


def program_files_dir():
    # we need the 32-bit key as all VS version are 32-bit for the forseeable future
    key='Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir'
    if common.is_win64():
        key='Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir (x86)'
    return common.read_reg(key)
        

def msvc_default_root(version):
    ''' returns known default paths, incase the reg or env fails'''
    ret=VC_ROOT_DEFAULTS.get(version,None) % program_files_dir()
    return ret

def msvs_default_root(version):
    ''' returns known default paths, incase the reg or env fails'''
    ret=msvc_default_root(version)
    if ret != None:
        ret= ret[:-len(VC_SUB_DIR[version])]
    return ret


def msvs_root_dir(version):
    ''' 
    Get the root MSVS install directory for a given version
    return None if there is an error
    '''

    if vs_root_cache.has_key(version)==True:
        return vs_root_cache[version]
    val=msvc_root_dir(version)
    if val != None:
        val= val[:-len(VC_SUB_DIR[version])]
        if os.path.isdir(val)==False:
            vs_root_cache[version]=None
            return None

    vs_root_cache[version]=val
    return val

def msvc_root_dir(version):
    ''' 
    Get the root MSVC install directory for a given version
    return None if there is an error
    '''
    if vc_root_cache.has_key(version)==True:
        return vc_root_cache[version]
    val=msvc_reg_root(version)
    if val == None or os.path.isdir(val)==False:
        val=msvc_env_root(version)
        if val == None or os.path.isdir(val)==False:
            val=msvc_default_root(version)
            if val == None or os.path.isdir(val)==False:
                vc_root_cache[version]=None
                return None

    vc_root_cache[version]=val
    return val

def framework_root():
    VS_HKEY_BASE="\\"
    if common.is_win64():
        VS_HKEY_BASE="\\Wow6432Node\\"
    key = 'Software%sMicrosoft\\.NETFramework\\InstallRoot' % (VS_HKEY_BASE)
    try:
        comps = common.read_reg(key)
        debug('Found framework dir in registry: %s' % comps)
    except WindowsError, e:
        debug('Did not find framework dir key %s in registry' % \
              (key))
        return ''
    return comps
    
def framework_root64():
    ''' currently this value when added seem to be messed up in the scripts
    on 32-bit OS systems. Since this path is always bad, we don't add it in these
    cases'''
         
    key = 'Software\\Microsoft\\.NETFramework\\InstallRoot'
    try:
        comps = common.read_reg(key)
        if comps[-3:] != '64\\':
            comps=comps[:-1]+'64\\'
            if os.path.exists(comps) == False:
                debug('Did not find framework64 dir')
                return ''
        debug('Found framework64 dir in registry: %s' % comps)
    except WindowsError, e:
        debug('Did not find framework64 dir key %s in registry' % \
              (key))
        return ''
    return comps

def get_current_sdk():
    ''' get SDK path based on reg key used for vc 9.0 and newer'''
    # note this key is used for both 32-bit and 64-bit systems
    # this mean the that default path will always be program file/xxx
    # even on 64-bit systems
    key='SOFTWARE\Microsoft\Microsoft SDKs\Windows\CurrentInstallFolder'
    try:
        dir=SCons.Util.RegGetValue(SCons.Util.HKEY_CURRENT_USER, key)[0]
        debug('Found SDK dir in registry: %s' % dir)
    except WindowsError, e:
        debug('Did not find SDK dir key %s in registry' % \
              (key))
    return dir
        

##def msCsharp_root_dir(version):
##    ''' 
##    Get the root C# install directory for a given version 
##    return None if there is an error
##    '''
##
##    val=msvs_root_dir(version)
##    val=os.path.join(val,'VC#')
##    if os.path.isdir(val):
##        return val
##    return None






