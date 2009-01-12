import parts.common as common
import SCons.Script
import os


###########################################
## Version mapping File Builder
###########################################

def scanner_function(node, env, path):

    ret=[]
    def_env=SCons.Script.DefaultEnvironment()
    alias=env['ALIAS']
    depends=def_env['PART_INFO'][alias]['DEPENDSON']

    for d in depends:
        val=d.resolve_alias(env)
        if val == "":
            #don't need to warn here as it was already warned by primary depends mapper
            continue
        ret.append(def_env['PART_INFO'][val]['FILE'])
    return ret        


def mapping_bf_str(target = None, source = None, env = None):
    return "Parts: Writing version mapping file for part alias ["+env['ALIAS']+']'
    
def mapping_bfe(target, source, env):
    # get target file
    tf= env.subst('$ALIAS')+'_'+env.subst('$PART_VERSION')
    # make new name
    tout=[os.path.join('$BUILD_DIR_ROOT',tf+'.version.mapping')]
    
    #env.Clean(env['ALIAS'],tout)
    return (tout,[])

def mapping_bf(target, source, env):
    f = open(str(target[0]), 'wb')
    def_env=SCons.Script.DefaultEnvironment()
    lst=def_env['PART_INFO'][env['ALIAS']]['DEPENDSON']
    f.write('PARTS: Mapping of dependents for part alias: '+env['ALIAS']+'\n')
    #print 'Mapping of dependents for part alias:',env['ALIAS']

    for i in lst:
        a=env.subst(i.alias_mapping_string())
        #print i,'expanded to part Alias:',a,'Name:',def_env['PART_INFO'][a]['NAME'],'Version:',def_env['PART_INFO'][a]['VERSION']
        if a == '':
            f.write(i.alias_mapping_string()+' was not defined in the SConstruct file')
        else:
            f.write(i.alias_mapping_string()+' expanded to Part -\n\tAlias: '+a+
            '\n\tName: '+str(env.subst(def_env['PART_INFO'][a]['NAME']))+
            '\n\tVersion: '+str(env.subst(def_env['PART_INFO'][a]['VERSION']))+'\n')
    if lst==[]:
        f.write("No dependents defined")
    print "PARTS: Writing -- Done"
    

common.AddBuilder('_MapUnknowns',SCons.Script.Builder(
        action = SCons.Script.Action(mapping_bf,mapping_bf_str),
        emitter=mapping_bfe,
        target_scanner=SCons.Script.DefaultEnvironment().Scanner(scanner_function)
        ))