import default_setting,query,common
import SCons.Util


'''
Notes on defaults for the different versions

vc 6 This version has 32-bit compiler
vc2002 (7) This version has 32-bit compiler
vc2003 (7.1) This version has 32-bit compiler
vc2005 (8.0) This version has 32-bit and 64-bit compilers
vc2008 (9.0) This version has 32-bit and 64-bit compilers

EXPRESS

vc2005 - This version will install in the same location as the std version. the main difference is that
the platform SDK is not installed. This means that it has to be setup independently. Does not contain 64-bit compilers

vc2008 - basically the same as professional. Need to check different Reg key to see if it is installed. 
However it will install in same default location as the std versions. Platform SDK is installed in seperate 
location. In this case the SDK will install in program file even on 64-bit systems ( different for what VS will do)
The current version it will use is version 6.0A. The script will use a key 
HKCU\SOFTWARE\Microsoft\Microsoft SDKs\Windows\CurrentInstallFolder
This is true for even 64-bit system ( ie not the WOW6432Node, however there seems to be a copy here as well)
Does not contain 64-bit compilers

'''

SupportedVCList=[
    {
    version:'6.0',
    hkey_root_vc:["Software%sMicrosoft\\VisualStudio\\6.0\\Setup\\Microsoft Visual C++\\ProductDir"],
    default_install_vc:'%s\\Microsoft Visual Studio\\VC98\\',
    common_tools_var:'VS60COMNTOOLS',
    vc_sub_dir:'VC98\\',
    batch_file:'vcvars32.bat',
    support_arch:['x86']
    },
    {
    version:'7.0',
    hkey_root_vc:["Software%sMicrosoft\\VisualStudio\\7.0\\Setup\\VC\\ProductDir"],
    default_install_vc:'%s\\Microsoft Visual Studio .NET\\VC7\\',
    common_tools_var:'VS70COMNTOOLS',
    vc_sub_dir:'VC7\\',
    batch_file:'vcvars32.bat',
    support_arch:['x86']
    },
    {
    version:'7.1',
    hkey_root_vc:["Software%sMicrosoft\\VisualStudio\\7.1\\Setup\\VC\\ProductDir"],
    default_install_vc:'%s\\Microsoft Visual Studio 7.1.NET 2003\\VC7\\',
    common_tools_var:'VS71COMNTOOLS',
    vc_sub_dir:'VC7\\',
    batch_file:'vcvars32.bat',
    support_arch:['x86']
    },
    {
    version:'8.0',
    hkey_root_vc:[
        "Software%sMicrosoft\\VisualStudio\\8.0\\Setup\\VC\\ProductDir",
        "Software%sMicrosoft\\VCExpress\\8.0\\Setup\\VS\\ProductDir"],
    default_install_vc:'%s\\Microsoft Visual Studio 8\\VC\\',
    common_tools_var:'VS80COMNTOOLS',
    vc_sub_dir:'VC\\',
    batch_file:'vcvars32.bat',
    support_arch:['x86','x86_64','ia64']
    },
    {
    version:'9.0',
    hkey_root_vc:[
        "Software%sMicrosoft\\VisualStudio\\9.0\\Setup\\VC\\ProductDir",
        "Software%sMicrosoft\\VCExpress\\9.0\\Setup\\VS\\ProductDir"
    ],
    default_install_vc:'%s\\Microsoft Visual Studio 9.0\\VC\\',
    common_tools_var:'VS90COMNTOOLS',
    vc_sub_dir:'VC\\',
    batch_file:'vcvars32.bat',
    support_arch:['x86','x86_64','ia64']
    }
]



class tool_settings:
    def __init__(self,env,version,use_bat,**kw):
        if version == None:
            v1=env.get('MSVC_VERSION',env.get('MSVS_VERSION',None))
            if v1 != None:
                self.version=v1
            else:
                self.ver=query.get_lastest_version(arch)
        elif SCons.Util.is_String(version)==False:
            self.version=str(version)
        else:
            self.version = version
        
        ## first validate we can build on platform cases
        # validate host build cases.
        host=env['HOST_SYSTEM']
        if host.Platform() in ['win32']:
            raise ValueError("Invalid Host Platform %s, only 'win32' is supported" % target.Platform())
        if host.Architecture() in ['x86','x86_64']:
            raise ValueError("Invalid Host Architecture %s, only 'x86' or 'x86_64' is supported" % target.Architecture())
        
        # validate cross build cases.. easy for windows in general
        target=env['TARGET_SYSTEM']
        if target.Platform() in ['win32']:
            raise ValueError("Invalid Target Platform %s, only 'win32' is supported" % target.Platform())
        if target.Architecture() in ['x86','x86_64']:
            raise ValueError("Invalid Target Architecture %s, only 'x86' or 'x86_64' is supported" % target.Architecture())
        self.target=target

        # validate this as a supported version
        if ver not in SUPPORTED_VERSIONS: 
            raise ValueError("Microsoft Version '%s', is not supported or invalid" % (ver))
        # check that this combo is found
        elif query.is_vc_known(ver,target.Architecture())==False:
            raise ValueError("Microsoft Version '%s', Architecture '%s' not found on system" % (ver,arch))        
        
        self.use_bat=use_bat
        

def get_shell_enviroment(env, ver, arch="x86"):
    '''this function returns the shell environment for a give version and architecture
    '''
    #first we need to get certain varible
    
    env['VCINSTALL']=rootpath.msvc_root_dir(ver)
    env['VSINSTALL']=rootpath.msvs_root_dir(ver)
    env['FRAMEWORK_ROOT']=rootpath.framework_root()
    env['FRAMEWORK_ROOT64']=rootpath.framework_root64()
    
    shellenv={
    'PATH':env.subst(get_path(ver,arch)),
    'INCLUDE':env.subst(get_include(ver,arch)),
    'LIB':env.subst(get_lib(ver,arch)),
    'LIBPATH':env.subst(get_libpath(ver,arch))
    }

    return shellenv


    
''' basic logic
if version == None find lastest version, or check on path in env if the CL exists
if target_arch == None find current OS bitness and use that as target architechture 
if use_bat == None or Bool(False) use default setting, 
if use_bat == Bool(True) use default cmd file, with arch based flags
if use_bat == (string) assume it point to cmd file to use


'''

def _setup_env(env,ts):
    # since in Parts we can have the orginal exist test happen instead of our
    # We need to verify that "smarter" test ran to setup the needed state
    if query.is_known == False:
        query.query_for_known()
    # this will be the ENV setup prepended to the shell
    shell_env=None
    #first we need to know the architechture
    arch =ts.target.Architecture()
    # next get the version
    ver=ts.version
      
    # Next we need to know if we should call a batch file or use default setting
    if ts.use_bat == False or ts.use_bat==None:
        shell_env = default_setting.get_shell_enviroment(env,ver,arch)       
        
    elif ts.use_bat==True:
        # in this case we need to get the path to the bat file
        # and run the script to get the env info
        pass
    elif is_string(ts.use_bat):
        #in this case we just check to see if the file exists
        #if so run script to get the Env values.
        pass
    else:
        # we have a bad value type
        # report error
        pass
    #take known info, get data, and set up env
    
    for k, v in shell_env.items():
            env.PrependENVPath(k, v, delete_existing=1)
    # replacement for MSVS_VERSION.. try to use as read only
    # but since tools start logic in SCons is unclear read as well for backwards
    # compatibility
    env['MSVC_VERSION']=ver 
    # just to be safe
    env['MSVS_VERSION']=ver # might change meaning to mean VS shell env's
    
    env['MSVS']={'FOUND_VC':common.FOUND_VC}
    
        
def setup_env(env,version=None,use_bat=False,**kw):
    _setup_env(env,tool_settings(version,arch,use_bat,**kw))
    
    
    
