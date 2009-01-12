'''
this file contains a set of varible used to hold default value for all platforms
such as flags. These may or may not be used by a given configuration, but exist
to help with the definition of such configuration and platforms.
'''

import SCons.Script 

### Base stuff for configurations

if SCons.Script.DefaultEnvironment()['PLATFORM'] == 'win32':
    platform_defines_release=['WIN32','_WINDOWS','_WIN32_WINNT=0x501','NDEBUG']
    platform_defines_debug=['WIN32','_WINDOWS','_WIN32_WINNT=0x501']
    # common libs that are useful to pull by default
    platform_base_libs_release=[]
    platform_base_libs_debug=[]
    platform_link_flags_release=[]
    platform_link_flags_debug=[]
    
elif SCons.Script.DefaultEnvironment()['PLATFORM'] == 'posix':
    platform_defines_release=[]
    platform_defines_debug=[]
    platform_base_libs_release=[]
    platform_base_libs_debug=[]
    platform_link_flags_release=['$__RPATH']
    platform_link_flags_debug=['$__RPATH']
elif SCons.Script.DefaultEnvironment()['PLATFORM'] == 'sunos':
    platform_defines_release=[]
    platform_defines_debug=[]
    platform_base_libs_release=[]
    platform_base_libs_debug=[]
    platform_link_flags_release=['$__RPATH']
    platform_link_flags_debug=['$__RPATH']
else:
    platform_defines_release=[]
    platform_defines_debug=[]
    platform_base_libs_release=[]
    platform_base_libs_debug=[]
    platform_link_flags_release=[]
    platform_link_flags_debug=[]
    
