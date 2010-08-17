
import parts.common as common
import parts.reporter as reporter
import parts.version as version
import SCons.Script

def part_version(env,ver=None):
    '''
    Defines the version of this part
    if no part is being defined it does nothing
    '''
    if ver == None:
        return get_part_version(env)

    part_obj=common.g_engine._part_manager._from_env(env)       
    ret=version.version(ver)
    if part_obj.Version != '0.0.0':
        reporter.report_warning("Version already set to %s, ignoring new value of %s"%(part_obj.Root.Version,ret))
        return part_obj.Version 
    part_obj._set_version(ret)
            
    return ret
    
def get_part_version(env):
    return common.g_engine._part_manager._from_env(env).Version

def get_part_short_version(env):
    return common.g_engine._part_manager._from_env(env).ShortVersion



# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object  
SConsEnvironment.PartVersion=part_version
SConsEnvironment.PartShortVersion=get_part_short_version