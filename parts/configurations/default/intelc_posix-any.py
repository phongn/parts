######################################
### Intel compiler configurations default-posix
######################################

import sys,os
from parts.config import *
import parts.version
import SCons.Script

def make_bool(obj):
    if obj is bool():
        return obj
    #assume string
    if obj.lower() == 'true':
        return True
    return False

def map_default_version(env):
    return env['INTELC_VERSION']

def post_process_func(env):
    # does not care if Intel Compiler version can or cannot
    # support given version. Compiler will complain if it can't

    try:
        ver=parts.version.version(env['GCC_VERSION'])
        ver=str(ver.major())+str(ver.minor())+str(ver.revision())
        #print env['GCC']['INSTALL_ROOT'],env['GCC']['TOOL']
        #print env['GXX']['INSTALL_ROOT'],env['GXX']['TOOL']
           
        env.Append(CCFLAGS=['-gcc-name='+os.path.join(env['GCC']['INSTALL_ROOT'],env['GCC']['TOOL']),
            '-gxx-name='+os.path.join(env['GXX']['INSTALL_ROOT'],env['GXX']['TOOL']),
            '-gcc-version='+ver])
    except:
        raise RuntimeError("You need to define gnutools or compatible tool chain with Intel tool chain")
    
    ## code coverage feature additions
    if make_bool(env.get('codecov',False)) == True:    
        if(env.Version(env['INTELC_VERSION']) >= 11):
            env.Append(CCFLAGS=['-prof-gen=srcpos'])
        else:
            env.Append(CCFLAGS=['-prof-genx'])



config=configuration(map_default_version,post_process_func)

                
