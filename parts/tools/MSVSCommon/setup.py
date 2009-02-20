import default_setting,query,common
import SCons.Util



class tool_settings:
    def __init__(self,version,arch,use_bat,**kw):
        if version == None:
            self.version = None
        elif SCons.Util.is_String(version)==False:
            self.version=str(version)
        else:
            self.version = version
        
        if arch==None:
            arch=common.ChipArchitecture()
        if arch != 'x86' and arch != 'x86_64':
            raise ValueError("Invalid architecture %s, only 'x86' or 'x86_64' is supported" % arch)
        self.arch=arch
        self.use_bat=use_bat
        pass
     
    
    
''' basic logic
if version == None find lastest version, or check on path in env if the CL exists
if arch == None find current OS bitness and use that as target architechture 
if use_bat == None or Bool(False) use default setting, 
if use_bat == Bool(True) use default cmd file, with arch based flags
if use_bat == (string) assume it point to cmd file to use


'''

def _setup_env(env,ts):
    # since in Parts we can have the orginal exist test happen instead of our
    # We need to verify that "smarter" test ran to setup the needed state
    if query.is_known == False:
        query.query_for_known()
    shell_env=None
    #first we need to know the architechture
    arch =ts.arch
    # next get the version
    ver=ts.version
    if ver==None:
        # get latest version
        ver=query.get_lastest_version(arch)
        #else we need to validate this as a supported version
    elif ver not in common.SUPPORTED_VERSIONSSTR: 
        raise ValueError("MSVS Version '%s', is not supported or invalid" % (ver))
    elif query.is_vc_known(ver,arch)==False:
        raise ValueError("MSVS Version '%s', Architecture '%s' not found on system" % (ver,arch))
    
    if env.get('MSVC_VERSION','0.0') == ver:
        return
      
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
    
    env.PrependENVPath('PATH',shell_env['PATH'])
    env.PrependENVPath('INCLUDE',shell_env['INCLUDE'])
    env.PrependENVPath('LIB',shell_env['LIB'])
    env.PrependENVPath('LIBPATH',shell_env['LIBPATH'])
    env['MSVS_VERSION']=ver
    env['MSVC_VERSION']=ver
    env['MSVS']={'FOUND_VC':common.FOUND_VC}
    
    #print env.Dump('ENV')
        
    

def setup_env(env,version=None,arch=None,use_bat=False,**kw):
    _setup_env(env,tool_settings(version,arch,use_bat,**kw))
    
    
    
