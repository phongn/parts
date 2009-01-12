
import parts.common as common
import parts.version as version
import SCons.Script

def part_version(env,ver=None):
    '''
    Defines the version of this part
    if no part is being defined it does nothing
    '''
    if ver == None:
        return get_part_version(env)
    def_env=SCons.Script.DefaultEnvironment()
    alias=def_env['DEFINING_PART']
    ret=version.version('0.0.0')
    if alias != None:
        part_info=def_env['PART_INFO'][alias]
        if part_info['PARENT_ALIAS']==None:
            ret=version.version(ver)
            part_info['VERSION']=ret
            part_info['SHORT_VERSION']=ret.short_version_string()
        else:
            tmp_info=def_env['PART_INFO'][part_info['PARENT_ALIAS']]
            while tmp_info['PARENT_ALIAS'] != None:
                tmp_info=def_env['PART_INFO'][tmp_info['PARENT_ALIAS']]
            
            part_info['VERSION']="${PARTS('"+tmp_info['ALIAS']+"','VERSION')}"
            part_info['SHORT_VERSION']="${PARTS('"+tmp_info['ALIAS']+"','SHORT_VERSION')}"
    return ret
    
def get_part_version(env):
    return version.version(env.subst('$PART_VERSION'))

def get_part_short_version(env):
    return version.version(env.subst('$PART_SHORT_VERSION'))



# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object  
SConsEnvironment.PartVersion=part_version
SConsEnvironment.PartShortVersion=get_part_short_version