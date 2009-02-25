
import SCons.Util

import default_setting,common

''' This file contains functions required to query the for existance of 
different version of VC. In general it is VC based.
'''

# used to see if this is query for known has been run already
# this is private to the query_for_known function.
_is_known = False

def query_for_known():
    '''
    Get known defaults and store them, so we can quickly access them latter
    '''
    global _is_known
    if _is_known==False:
        _is_known=True
        for v in SupportedVCList:
            for arch in vs['support_arch']:
                vs=VisualStudio(target_arch=arch,**v)
                val=vs.cl_exists()#_msvc_exists('cl',arch,True)
                if val == True:
                    FOUND_VC[arch]
                    FOUND_VC[arch][v['version']]=vs

def is_vc_known(version,arch):
    ''' 
    Do we know if a certain version exists or not
    '''
    query_for_known()
    if version in common.FOUND_VC.get(arch,[]):
        return True
    return False

def get_lastest_version(arch):
    ''' 
    Get the latest version known based on target architecture
    '''
    query_for_known()
    try:
        ret=common.FOUND_VC.get(arch,[None])[0].version
    except Exception,ec:
        return None
    return ret

def msvc_exists(env,tool,version=None,arch=None,strict=False):
    '''
    see _msvc_exists for details
    '''
    
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
    
    NOTE!! the env here is ment to be const, "read only" as we are find if something
    is true. We are not setting values yet
    '''
    if arch==None:
        arch=common.ChipArchitecture()
    if arch != 'x86' and arch != 'x86_64' and arch != 'ia64':
        raise ValueError("Invalid architecture %s, only 'x86' or 'x86_64' or 'ia64' is supported" % arch)
    
    if version == None and arch==None:
        # Get all known paths
        for v in FOUND_VC[arch].itervalues():
            p+=v.get_path()
    else:
        # Get path if found else return false
        if FOUND_VC[arch].has_key(version):
            p=FOUND_VC[arch][version].get_path()
        else:
            return False
    
    #try with the known paths and what ever is in the SCons enviroment
    tmp=SCons.Util.WhereIs(tool,path=p)
    if tmp!=None:
        # This if block validates that in the case of finding the x86_64
        # version of the tool, we don't get a false positive of a 32-bit version
        # This happens because the path is in the general form of (for 64-bit only)
        # vcbin_arch;vcbin;...   
        # Which means that two CL can exist on the path, but since the vcbin_arch 
        # form is first it is found first. if it was not there or installed we would
        # get a false postive.
        if version != None and arch == 'x86_64':
            if tmp.find('amd64') == -1:
                return False
        elif version != None and arch == 'ia64':
            if tmp.find('ia64') == -1:
                return False
        return True

    return False
            