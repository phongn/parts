#########################
## Intel(R) configurations

import SCons.Script 
from parts.config_base import *
from parts.config import *
import parts.common as common

g_env=SCons.Script.DefaultEnvironment()

def icl_post_config(map):
    # If we are on Windows, we want to make sure the correct flags are being used.
    # To do this, we check to see what version of the MS compiler we are using
    # and then we set the needed flags.
    if g_env['PLATFORM'] == 'win32':            
        if map.has_key('MSVS_VERSION'):
            v=map['MSVS_VERSION']
        else:
            if g_env['MSVS_VERSION'][-3:]=='Exp':
                 g_env['MSVS_VERSION']= g_env['MSVS_VERSION'][:-3]
            v=g_env['MSVS_VERSION']
        if v=='6.0':
            map['CCFLAGS'].extend(['/Qvc6'])
        elif v=='7.0':
            map['CCFLAGS'].append('/Qvc7')
        elif v=='7.1':
            map['CCFLAGS'].append('/Qvc7.1')
        # this case need better test as 9.0 and below do not support vc8.0
        elif v=='8.0':
            map['CCFLAGS'].append('/Qvc8')
    codecov=common.option_bool(SCons.Script.ARGUMENTS.get('codecov', False),'codecov',False)
    if codecov==True:
        if g_env['PLATFORM'] == 'win32':
            map['CCFLAGS'].append('/Qprof-genx')
        else:
            map['CCFLAGS'].append('-prof-genx')
    
def icl_tool_add(map,tool,ver,config):
    # map icc and icl to the same tool (help with Linux/Window differences)
    if tool=='icc':
        tool='intelc'
    if tool=='icl':
        tool='intelc'
    # set up version of tool to use
    if ver==None:
        map['tools']=[(tool,{'abi': None, 'verbose':1})]
    else:
        if g_env['PLATFORM'] == 'posix':
            v=ver
        else:
            #if float(ver[:3]) < 10.0:
            #    v=str(int(float(ver)*10))
                #if v=='7.1': v='7.0'
            #else:
                #v=ver
            v=ver
            if v=='7.1': v='7.0'
            
            
        ##print "***",v,ver
        map['tools']=[(tool,{'abi': None,'version':v,'verbose':1})]
    # setup this tool to get a post config pass to setup any last minute flags
    # that depend on the configured verion of MS or GCC compiler
    
    if g_env['PLATFORM'] == 'win32':
        map['WINDOWS_INSERT_MANIFEST']=1
        # fixes the manifest issue with linking
        map['tools']=['msvc','mslink']+map['tools']
        # This line force the use of xilink over link 
        #( which is what we might want todo )
        map['LINK']='xilink'
        
    map['post_config']=[icl_post_config]
        
    return True

if g_env['PLATFORM'] == 'win32':
    Intel_CCFLAGS_debug=['/nologo','/Od','/MDd','/W3','/Zc:wchar_t','/RTC1']
    Intel_CCFLAGS_release=['/nologo','/Ox','/MD','/W3','/Zc:wchar_t']
    Intel_CXXFLAGS_debug=['$CCFLAGS','/EHsc','/GR']
    Intel_CXXFLAGS_release=['$CCFLAGS','/EHsc','/GR']
    Intel_link_flags_release=platform_link_flags_release+['/nodefaultlib:"libmmd.lib"']
    Intel_link_flags_debug=platform_link_flags_debug+['/nodefaultlib:"libmmdd.lib"']
elif g_env['PLATFORM'] == 'posix':
    Intel_CCFLAGS_debug=['-O0', '-g']
    Intel_CCFLAGS_release=['-O2']
    Intel_CXXFLAGS_debug=['$CCFLAGS']
    Intel_CXXFLAGS_release=['$CCFLAGS']
    Intel_link_flags_release=platform_link_flags_release+['-i-static']
    Intel_link_flags_debug=platform_link_flags_debug+['-i-static']
elif g_env['PLATFORM'] == 'sunos':
    Intel_CCFLAGS_debug=['-O0', '-g']
    Intel_CCFLAGS_release=['-O2']
    Intel_CXXFLAGS_debug=['$CCFLAGS']
    Intel_CXXFLAGS_release=['$CCFLAGS']
    Intel_link_flags_release=platform_link_flags_release+['-i-static']
    Intel_link_flags_debug=platform_link_flags_debug+['-i-static']
else: 
    Intel_setting_debug=[]
    Intel_setting_release=[]
    Intel_link_flags_release=platform_link_flags_release
    Intel_link_flags_debug=platform_link_flags_debug



configuration('release','icl','7.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','7.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','7.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','7.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

configuration('release','icl','7.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','7.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','7.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','7.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

configuration('release','icl','8.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','8.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','8.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','8.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

configuration('release','icl','8.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','8.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','8.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','8.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)


configuration('release','icl','9.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','9.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','9.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','9.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

configuration('release','icl','9.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','9.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','9.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','9.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

configuration('release','icl','10.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','10.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','10.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','10.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
            

configuration('release','icl','10.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','10.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','10.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','10.1',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
            
configuration('release','icl','11.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl','11.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc','11.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc','11.0',icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

configuration('release','icl',None,icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icl',None,icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)
configuration('release','icc',None,icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_release,CXXFLAGS=Intel_CXXFLAGS_release,
            CPPDEFINES=platform_defines_release,
            LINKFLAGS=Intel_link_flags_release,
            LIBS=platform_base_libs_release)
configuration('debug','icc',None,icl_tool_add,
            CCFLAGS=Intel_CCFLAGS_debug,CXXFLAGS=Intel_CXXFLAGS_debug,
            CPPDEFINES=platform_defines_debug,
            LINKFLAGS=Intel_link_flags_debug,
            LIBS=platform_base_libs_debug)

