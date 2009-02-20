
import SCons.Util

import default_setting,common

is_known = False
def query_for_known():
    '''
    Get known defaults and store them, so we can quickly access them latter
    '''
    global is_known
    if is_known==False:
        is_known=True
        for v in common.SUPPORTED_VERSIONSSTR:
            for arch in ['x86','x86_64']:
                val=_msvc_exists('cl',v,arch,True)
                if val == True:
                    common.FOUND_VC[arch].append(v)
        

def is_vc_known(version,arch):
    if version in common.FOUND_VC.get(arch,[]):
        return True
    return False

def get_lastest_version(arch):
    try:
        ret=common.FOUND_VC.get(arch,[None])[0]
    except Exception,ec:
        return None
    return ret

def msvc_exists(env,tool,version=None,arch=None,strict=False):
    query_for_known()
    return _msvc_exists(tool,version,arch,strict)
    
def _msvc_exists(tool,version=None,arch=None,strict=False):
    '''
    this will validate we have a CL compiler, or linker or ML (masm) as well as 
    any other basic MS tools needed given a C++ enviroment. 
    
    tool is the tools we want to find
    version the version of the tool. if None try all known version
    Arch is the architecture to try given default architechture
    string only valid is version is not None. will do simple check to see if
    the tools is in a 64-bit path not a 32-bit one.
    
    
    Other forms of this 
    may be created to help with C# or other languages that can be built with MSVS
    
    NOTE!! the env here is ment to be const, "read only" as we are find if something
    is true. We are not setting values yet
    '''
    if arch==None:
        arch=common.ChipArchitecture()
    if arch != 'x86' and arch != 'x86_64':
        raise ValueError("Invalid architecture %s, only 'x86' or 'x86_64' is supported" % arch)
     
    
    if version == None and arch==None:
        # GetMSVCPath() will return all known defaults
        p=default_setting.GetMSVCPath()
    else:
        # we want a given version and architecture
        # Note if arch is None it will try to get the OS architure and use that
        p=default_setting.GetMSVCPath(version,arch)
    
    #try with the known paths and what ever is in the SCons enviroment
    
    tmp=SCons.Util.WhereIs(tool,path=p)
    if tmp!=None:
        if version != None and arch != 'x86':
            if tmp.find('amd64') == -1:
                return False
        return True

    return False
            