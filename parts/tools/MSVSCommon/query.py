
import SCons.Util

import common,vs
import part_compat

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
        for v in common.SupportedVCList:
            for arch in v['support_arch']:
                tmp=vs.VisualStudio(target_arch=arch,**v)
                val=tmp.cl_exists()
                if val == True:
                    common.FOUND_VC[arch][v['version']]=tmp


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
        tmp=common.FOUND_VC['x86'].keys()
        tmp.sort()
        ret=tmp[-1]
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
    ## validate inputs
    if arch==None:
        arch=part_compat.ChipArchitecture()
    if arch != 'x86' and arch != 'x86_64' and arch != 'ia64':
        raise ValueError("Invalid architecture %s, only 'x86' or 'x86_64' or 'ia64' is supported" % arch)
    ## get result
    if version == None:
        # Get all known paths
        for v in common.FOUND_VC[arch].itervalues():
            if v.exists(tool,strict):
                return True
    else:
        # Get path if found else return false
        version=str(version)
        if common.FOUND_VC[arch].has_key(version):
            return common.FOUND_VC[arch][version].exists(tool,strict)
    
    return False
    
    
            