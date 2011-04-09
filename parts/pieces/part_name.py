import parts.glb as glb
import parts.api as api

import SCons.Script

def part_name(env,id=None,parent_name=None):
    '''Defines the ID or name the developer uses to name this "part".
    Many different versions of a given part can be defined during a build.
    This allow the developer to ID what this component is and a way to later
    define DependOn(...) logic for his component
    '''
    if id == None:
        return get_part_name(env)
    
    alias=env['PART_ALIAS']
    if alias != None:
        part_obj=glb.engine._part_manager._from_env(env)
        if parent_name is not None:
            part_obj._set_name(id,parent_name)
        else:
            part_obj.ShortName=id
        return part_obj.Name
    return None

def get_part_name(env):
    return glb.engine._part_manager._from_env(env).Name

def get_part_short_name(env):
    return glb.engine._part_manager._from_env(env).ShortName

class _PartName(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,name=None):
        part_name(name)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# add global for new format
api.register.add_global_parts_object('PartName',_PartName)

# adding logic to Scons Enviroment object  
SConsEnvironment.PartName=part_name
SConsEnvironment.PartShortName=get_part_short_name
