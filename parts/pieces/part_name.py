
import parts.common as common
import SCons.Script

def part_name(env,id=None,parent_name=None):
    '''Defines the ID or name the developer uses to name this "part".
    Many different versions of a given part can be defined during a build.
    This allow the developer to ID what this component is and a way to later
    define DependOn(...) logic for his component
    '''
    if id == None:
        return get_part_name(env)
    def_env=SCons.Script.DefaultEnvironment()
    alias=def_env['DEFINING_PART']
    if alias != None:
        parent=def_env['PART_INFO'][alias]['PARENT_ALIAS']
        #print 'Parent',parent
        if parent_name !=None:
            def_env['PART_INFO'][alias]['NAME']=parent_name+'.'+id
        elif parent == None:
            def_env['PART_INFO'][alias]['NAME']=id
        elif def_env['PART_INFO'][parent]['NAME']!=None:
            def_env['PART_INFO'][alias]['NAME']=def_env['PART_INFO'][parent]['NAME']+'.'+id
        else:
            pass # unknown at this time
            #def_env['PART_INFO'][alias]['NAME']="${PARTS('"+parent+"','NAME')}."+id
        def_env['PART_INFO'][alias]['SHORT_NAME']=id
        mid=def_env['PART_INFO'][alias]['NAME']
        #print 'part name',mid
        #print 'short part name',id
        
        if mid != None:
            # See that PART_IDS was setup
            if def_env.has_key('PART_IDS')==False:
                def_env['PART_IDS']={}
            # See that the ID Alias list exists
            if mid not in def_env['PART_IDS']:
                def_env['PART_IDS'][mid]=[]
            # Append to the ID list with new alias
            def_env['PART_IDS'][mid].append(alias)
                    
        return mid
    return None

def get_part_name(env):
    return env.subst('$PART_NAME')

def get_part_short_name(env):
    return env.subst('$PART_SHORT_NAME')



# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object  
SConsEnvironment.PartName=part_name
SConsEnvironment.PartShortName=get_part_short_name
