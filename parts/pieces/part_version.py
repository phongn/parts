import parts.glb as glb
import parts.api as api
import parts.api.output as output
import parts.version as version
import SCons.Script

def part_version(env,ver=None):
    '''
    Defines the version of this part
    if no part is being defined it does nothing
    '''
    if ver == None:
        return get_part_version(env)

    part_obj=glb.engine._part_manager._from_env(env)       
    ret=version.version(ver)
    if part_obj.Version != '0.0.0' and ret != part_obj.Version and part_obj.LoadState != glb.load_cache:
        api.output.warning_msg("Version already set to %s, ignoring new value of %s"%(part_obj.Root.Version,ret))
        return part_obj.Version 
    part_obj.Version=ret
            
    return ret
    
def get_part_version(env):
    return glb.engine._part_manager._from_env(env).Version

def get_part_short_version(env):
    return glb.engine._part_manager._from_env(env).ShortVersion

class _PartVersion(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,ver=None):
        part_version(ver)
        
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# add global for new format
api.register.add_global_parts_object('PartVersion',_PartVersion)

# adding logic to Scons Enviroment object  
SConsEnvironment.PartVersion=part_version
SConsEnvironment.PartShortVersion=get_part_short_version