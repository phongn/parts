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
                                '--sysroot=${GXX.SYS_ROOT}',
                                '-O2',
                                '-march=armv7-a',
                                '-mfloat-abi=softfp',
                            ],
                        CPPDEFINES=['DEBUG'],
                        LINKFLAGS=[
                                '--sysroot=${GXX.SYS_ROOT}',
                                '-Wl,--fix-cortex-a8'
                                   ],
                        LIBPATH=[
                                '${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/armeabi-v7a'
                                ],
                        LIBS=['gnustl_shared']
                        )
                    )

