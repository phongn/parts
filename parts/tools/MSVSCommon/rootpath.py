
from common import debug
import common
import SCons.Util

import os

#these keys tell us a given version of the compiler is installed
# they will not let us know that a given compiler architecture is installed
# a list is used as some compiler can be installed in different packages
##_VC_HKEY_ROOT = {
##'6.0':["Software%sMicrosoft\\VisualStudio\\6.0\\Setup\\Microsoft Visual C++\\ProductDir"],
##'7.0':["Software%sMicrosoft\\VisualStudio\\7.0\\Setup\\VC\\ProductDir"],
##'7.1':["Software%sMicrosoft\\VisualStudio\\7.1\\Setup\\VC\\ProductDir"],
##'8.0':["Software%sMicrosoft\\VisualStudio\\8.0\\Setup\\VC\\ProductDir","Software%sMicrosoft\\VCExpress\\8.0\\Setup\\VS\\ProductDir"],
##'9.0':["Software%sMicrosoft\\VisualStudio\\9.0\\Setup\\VC\\ProductDir","Software%sMicrosoft\\VCExpress\\9.0\\Setup\\VS\\ProductDir"]
##}
##
##VC_ROOT_DEFAULTS = {
##'6.0':'%s\\Microsoft Visual Studio\\VC98\\',
##'7.0':'%s\\Microsoft Visual Studio .NET\\VC7\\',
##'7.1':'%s\\Microsoft Visual Studio 7.1.NET 2003\\VC7\\',
##'8.0':'%s\\Microsoft Visual Studio 8\\VC\\',
##'9.0':'%s\\Microsoft Visual Studio 9.0\\VC\\'
##}
##
##VC_SUB_DIR = {
##'6.0':'VC98\\',
##'7.0':'VC7\\',
##'7.1':'VC7\\',
##'8.0':'VC\\',
##'9.0':'VC\\'
##}



def program_files_dir():
    # we need the 32-bit key as all VS version are 32-bit for the forseeable future
    key='Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir'
    if common.is_win64():
        key='Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir (x86)'
    return common.read_reg(key)
        

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
        




