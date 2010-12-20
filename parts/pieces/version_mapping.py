import parts.common as common
import SCons.Script
import os


###########################################
## Version mapping File Builder
###########################################

def scanner_function(node, env, path):

    ret=[]
    pobj=common.g_engine._part_manager._from_env(env)
    
    for d in pobj.Depends:
        if d.part:
            if d.part._file:           
                ret.append(d.part._file)
        else:
            reporter.report_warning('Part "{0}" depends on "{1}", however this Parts was not defined.'.format(pobj.Name,d.name),stackframe=d.stackframe)
    return ret        


def mapping_bf_str(target = None, source = None, env = None):
    return "Parts: Writing version mapping file for part alias ["+env['ALIAS']+']'
    
def mapping_bfe(target, source, env):
    # get target file
    pobj=common.g_engine._part_manager._from_env(env)
    tf= "%s_%s"%(pobj.Alias,pobj.Version)
    # make new name
    tout=[os.path.join('$BUILD_DIR_ROOT',tf+'.version.mapping')]
    
    #env.Clean(env['ALIAS'],tout)
    return (tout,[])

def mapping_bf(target, source, env):
    f = open(str(target[0]), 'wb')
    pobj=common.g_engine._part_manager._from_env(env)
    
    f.write('PARTS: Mapping of dependents for part Alias: %s Name: %s Version: %s\n'%(pobj.Alias,pobj.Name,pobj.Version))
    
    for i in pobj.Depends:
        if i.part is None:
            f.write(i.alias_mapping_string()+' was not defined in the SConstruct file')
        else:
            f.write('%s expanded to Part -\n\tAlias: %s\n\tName: %s\n\tVersion: %s\n'%(i.alias_mapping_string(),i.part.Alias,i.part.Name,i.part.Version))
    if pobj.Depends==[]:
        f.write("No dependents defined")
    print "PARTS: Writing -- Done"
    

common.AddBuilder('_MapUnknowns',SCons.Script.Builder(
        action = SCons.Script.Action(mapping_bf,mapping_bf_str),
        emitter=mapping_bfe,
        target_scanner=SCons.Script.DefaultEnvironment().Scanner(scanner_function)
        ))