######################################
### Microsoft compiler configurations
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script
import re

g_env=SCons.Script.DefaultEnvironment()

#ignores the exp stuff at this time
# meant to clean up the 7.1exp from the 7.1
# current issues are that ms seem to have released 8.0exp as the express version
# and uses the same key is you have the 8.0 vsip installed
def vc_version():
    ms_ver_reg = re.compile(r'(\d+\.\d+)(.*)')
    version,exp=ms_ver_reg.match(g_env['MSVS_VERSION']).groups()
    return float(version)

def MS_deftool_add(map,tool,ver,config):
    #map['tools']=['msvc']
    v=vc_version()
    if v > 8.0:
        v=8.0
    map.update(get_config(config,'cl',str(v)))

    return True


def MS_tool_add(map,tool,ver,config):
    if ver == None:
        ver = vc_version()

    map['tools']=[('msvc', {'version':ver, 'abi':None}),('mslink', {'version':ver, 'abi':None})]
    #print '******',ver
    MS_lib_set(map,tool,ver,config)
    return True

def MS_lib_set(map,tool,ver,config):
    if ver==None:
        ver=vc_version()
        
    map['MSVS_VERSION']=ver
    map['MSVS_USE_MFC_DIRS']=1
    map['WINDOWS_INSERT_MANIFEST']=1
    map['MSVS_IGNORE_IDE_PATHS']=1
    return True


if sys.platform=='win32':
    # define only on Windows systems
    vc_6_ccflags_debug=['/nologo','/Od','/MDd','/W3','/GZ']
    vc_6_ccflags_release=['/nologo','/Ox','/MD','/W3']
    vc_6_cxxflags_debug=['$CCFLAGS','/EHsc','/GR']
    vc_6_cxxflags_release=['$CCFLAGS','/EHsc','/GR']

    vc_70_ccflags_debug=['/nologo','/Od','/MDd','/W3','/Zc:wchar_t','/RTC1']
    vc_70_ccflags_release=['/nologo','/Ox','/MD','/W3','/Zc:wchar_t']
    vc_70_cxxflags_debug=['$CCFLAGS','/EHsc','/GR']
    vc_70_cxxflags_release=['$CCFLAGS','/EHsc','/GR']

    vc_71_ccflags_debug=['/nologo','/Od','/MDd','/W3','/Zc:wchar_t','/RTC1']
    vc_71_ccflags_release=['/nologo','/Ox','/MD','/W3','/Zc:wchar_t']
    vc_71_cxxflags_debug=['$CCFLAGS','/EHsc','/GR']
    vc_71_cxxflags_release=['$CCFLAGS','/EHsc','/GR']

    vc_80_ccflags_debug=['/nologo','/Od','/MDd','/W3','/Zc:wchar_t','/RTC1']
    vc_80_ccflags_release=['/nologo','/Ox','/MD','/W3','/Zc:wchar_t']
    vc_80_cxxflags_debug=['$CCFLAGS','/EHsc','/GR']
    vc_80_cxxflags_release=['$CCFLAGS','/EHsc','/GR']

    # the VC 6 compiler
    configuration('release','cl','6.0',MS_tool_add,
                  CCFLAGS=vc_6_ccflags_release,
                  CXXFLAGS=vc_6_cxxflags_release,
                  CPPDEFINES=platform_defines_release,
                  LINKFLAGS=platform_link_flags_release,
                  LIBS=platform_base_libs_release)
    configuration('debug','cl','6.0',MS_tool_add,
                  CCFLAGS=vc_6_ccflags_debug,
                  CXXFLAGS=vc_6_cxxflags_debug,
                  CPPDEFINES=platform_defines_debug,
                  LINKFLAGS=platform_link_flags_debug,
                  LIBS=platform_base_libs_debug)
    # the VC 7 compiler
    configuration('release','cl','7.0',MS_tool_add,
                  CCFLAGS=vc_70_ccflags_release,
                  CXXFLAGS=vc_70_cxxflags_release,
                  CPPDEFINES=platform_defines_release,
                  LINKFLAGS=platform_link_flags_release,
                  LIBS=platform_base_libs_release)
    configuration('debug','cl','7.0',MS_tool_add,
                  CCFLAGS=vc_70_ccflags_debug,
                  CXXFLAGS=vc_70_cxxflags_debug,
                  CPPDEFINES=platform_defines_debug,
                  LINKFLAGS=platform_link_flags_debug,
                  LIBS=platform_base_libs_debug)
    # the VC 7.1 compiler
    configuration('release','cl','7.1',MS_tool_add,
                  CCFLAGS=vc_71_ccflags_release,
                  CXXFLAGS=vc_71_cxxflags_release,
                  CPPDEFINES=platform_defines_release,
                  LINKFLAGS=platform_link_flags_release,
                  LIBS=platform_base_libs_release)
    configuration('debug','cl','7.1',MS_tool_add,
                  CCFLAGS=vc_71_ccflags_debug,
                  CXXFLAGS=vc_71_cxxflags_debug,
                  CPPDEFINES=platform_link_flags_debug,
                  LIBS=platform_base_libs_debug)
    # the VC 8.0 compiler
    configuration('release','cl','8.0',MS_tool_add,
                  CCFLAGS=vc_80_ccflags_release,
                  CXXFLAGS=vc_80_cxxflags_release,
                  CPPDEFINES=platform_defines_release,
                  LINKFLAGS=platform_link_flags_release,
                  LIBS=platform_base_libs_release,
                  MSVS_USE_MFC_DIRS=1)
    configuration('debug','cl','8.0',MS_tool_add,
                  CCFLAGS=vc_80_ccflags_debug,
                  CXXFLAGS=vc_80_cxxflags_debug,
                  CPPDEFINES=platform_defines_debug,
                  LINKFLAGS=platform_link_flags_debug,
                  LIBS=platform_base_libs_debug,
                  MSVS_USE_MFC_DIRS=1)

# Get the latest version we can find and set the setting to this.
# This will, for example, set v8.0 (given that it is not defined).
# with the same setting as the latest version we have (7.1). This may
# not be correct, but it the best guess we have.

    configuration('release','cl',None,MS_deftool_add)
    configuration('debug','cl',None,MS_deftool_add)
    configuration('default','cl',None,MS_deftool_add)

    # the CRT level - useful for the Intel compiler, or other tools.

    configuration('default','mscrt','6.0',MS_lib_set)
    configuration('default','mscrt','7.0',MS_lib_set)
    configuration('default','mscrt','7.1',MS_lib_set)
    configuration('default','mscrt','8.0',MS_lib_set)
    configuration('default','mscrt',None,MS_lib_set)
