######################################
### Intel compiler configurations default
######################################

import sys
from parts.config import *
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
        ver=float(env['MSVC_VERSION'])
    except:
        raise RuntimeError("You need to define mstools or compatible tool chain with Intel tool chain")
    if ver >=10:
        env.AppendUnique(CCFLAGS=['/Qvc10'])
    elif ver >=9:
        env.AppendUnique(CCFLAGS=['/Qvc9'])
    elif ver >=8:
        env.AppendUnique(CCFLAGS=['/Qvc8'])
    elif ver >=7.1:
        env.AppendUnique(CCFLAGS=['/Qvc7.1'])
    elif ver >=7:
        env.AppendUnique(CCFLAGS=['/Qvc7'])
    elif ver >=6:
        env.AppendUnique(CCFLAGS=['/Qvc6'])
    
    ## code coverage feature additions
    if make_bool(env.get('codecov',False)) == True:    
        if(env.Version(env['INTELC_VERSION']) >= 11):
            env.AppendUnique(CCFLAGS=['/Qprof-gen:srcpos'])
        else:
            env.AppendUnique(CCFLAGS=['/Qprof-genx'])


config=configuration(map_default_version,post_process_func)

config.VersionRange("7-*",
                    append=ConfigValues(
                        CPPDEFINES=['WIN32','_WINDOWS'],
                        CCFLAGS=['/DINTELC_VERSION=$INTELC_VERSION']
                        )
                    )
    



