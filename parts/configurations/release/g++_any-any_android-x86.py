######################################
### gcc compiler configurations for android 
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['GXX_VERSION']
    
config=configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=[
                                '-O2',
                                '--sysroot=${GXX.SYS_ROOT}'
                            ],
                        CPPDEFINES=['NDEBUG'],
                        LINKFLAGS=[
                                '--sysroot=${GXX.SYS_ROOT}'
                                ],
                        LIBPATH=[
                                '${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/x86'
                                ],
                        LIBS=['gnustl_shared']
                        )
                    )

