import glb
import pattern
import common
import api.output
import errors

import SCons.Script

import os
import re

 
class EXPORT_TYPES(object):
    FILE=1
    PATH=2
    PATH_FILE=3


def export_path(env,target_dirs,source_dirs,pobj,prop,use_src=False,create_sdk=True):
    
    # We have three case basicaly of type of paths we pass
    # 1) is the SDK/final path for the file
    # 2) is the build path for the file
    # 3) is the source pasth of the file
    ret=[]
    tmp=pobj.DefiningSection.Exports[prop]
    if use_src: # ie use Raw Source Directories
        for s in source_dirs:
            # setting up the libpaths
            #print s,env.Dir(s).abspath
            if s not in tmp:
                target_dir=env.Dir(s).srcnode().abspath
                tmp.append(target_dir)
            # we want to return the SDK directories
            # when we need to create an SDK.
            if create_sdk==True:
                for t in target_dirs:
                # make this a node
                    if common.is_string(t):
                        t=env.Dir(t)
                    final_path=t.srcnode().abspath
                    if final_path not in tmp:
                        target_dir=final_path
                        ret.append(target_dir)
    else:
        for t in target_dirs:
            # make this a node
            if common.is_string(t):
                t=env.Dir(t)
                
            build_path=t.abspath
            final_path=t.srcnode().abspath
            
            if create_sdk==False:
                # use build directory
                if build_path not in tmp:
                    target_dir=build_path
                    tmp.append(target_dir)
                
            elif final_path not in tmp:
                target_dir=final_path
                tmp.append(target_dir)
                ret.append(target_dir)
    return ret

_reg=re.compile('[\w\-\.]*.so.([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)', re.I)
             
def export_file(env,targets,pobj,prop):
    ret=[]
    for t in targets:
        if common.is_string(t):
            t=env.File(t)
        file=os.path.split(t.abspath)[1]
        ret.append(file)
        
        if file.endswith('.so') or file.endswith('.sl'):
            file = file[:-3]
        elif _reg.match(file):
            # if this matches we want to not add this file
            # as doing this would upset the linker
            continue
        elif getattr(t.attributes,'pdb_owner',None):
            continue
        
        pobj.DefiningSection.Exports[prop]=[file]+pobj.DefiningSection.Exports[prop]
        
    return ret

def export_file_path(env,targets,pinfo,prop,use_src):
    ret=[]
    prop_val=pobj.DefiningSection.Exports[prop]
    for t in targets:
        if common.is_string(t):
            t=env.File(t)
        build_path=t.abspath
        final_path=t.srcnode().abspath
        ret.append(final_path)
        if use_src==False:
            # use build directory
            if build_path not in pinfo[prop]:
                prop_val.append(build_path)
        elif final_path not in pinfo[prop]:
                prop_val.append(final_path)
    return ret


def ExportCPPPATH(env,values,create_sdk=True):
    if common.is_list(values)==False:
        values=[values]
    values=SCons.Script.Flatten(values)
    v=[]
    for i in values:
        v.append(env.AbsDir(i))
    return ExportItem(env,'CPPPATH',v,create_sdk)
def ExportCPPDEFINES(env,values,create_sdk=True):
    return ExportItem(env,'CPPDEFINES',values,create_sdk)
def ExportCFLAGS(env,values,create_sdk=True):
    return ExportItem(env,'CFLAGS',values,create_sdk)
def ExportCCFLAGS(env,values,create_sdk=True):
    return ExportItem(env,'CCFLAGS',values,create_sdk)
def ExportCXXFLAGS(env,values,create_sdk=True):
    return ExportItem(env,'CXXFLAGS',values,create_sdk)
def ExportLINKFLAGS(env,values,create_sdk=True):
    return ExportItem(env,'LINKFLAGS',values,create_sdk)
def ExportLIBS(env,values,create_sdk=True):
    return ExportItem(env,'LIBS',values,create_sdk)

#def _map_group(x,group):
#    import metatag
#    if isinstance(x,SCons.Node.Node):
#        tmp=metatag.MetaTagValue(x,'dependgroup','parts',[])
#        tmp.append(group)
#        metatag.MetaTag(x,ns='parts',dependgroup=tmp)

def ExportItem(env,variable,values,create_sdk=True,map_as_depenance=False):#, public=False):
    '''
    
    @param env The current environment
    @param variable The variable name we want to export
    @param values The values to map to the variable. Can be an picklable item, including self contained functions, and SCons node objects
    @param create_sdk map this information in to the auto generated SDK parts file
    ##@param public Maps variable 'foo' to env['foo'] if False, else maps data only to a private namespace object of the form env[<component name>]['foo']
    
    This function adds to the export table of a given part the variable and it values. If the variable exists in the environment already and is a list or is the values is 
    a list type then the values will be made into a list, flatten and appended all unique items to the list. Otherwise the data will replace any existing data. If data does 
    exist, there will be a verbose message that can be printed out.
    '''
    
    errors.SetPartStackFrameInfo(True)
    pobj=glb.engine._part_manager._from_env(env)
    
    # test to see if the variable or value should be a list.
    # ie if the variable is a list in the Environment, we want this to be a list here
    if common.is_list(values) or common.is_list(env.get(variable)):
        
        values=common.make_list(values)
        #map(lambda x:  _map_group(x,variable),values)
        if pobj.DefiningSection.Exports.has_key(variable)==False:
            pobj.DefiningSection.Exports[variable]=[]
        # this is not a list already.. make it one
        if common.is_list(pobj.DefiningSection.Exports[variable]) == False:
            pobj.DefiningSection.Exports[variable]=common.make_list(pobj.DefiningSection.Exports[variable])
        
        # add our values
        #common.extend_unique(pobj.DefiningSection.Exports[variable],values)
        pobj.DefiningSection.Exports[variable]+=values
        
    else:
        if pobj.DefiningSection.Exports.has_key(variable):
            api.output.verbose_msg(['export'],'Part "{0}" already as variable "{1}" in export table, overriding with new value'.format(pobj.Name,variable))
        pobj.DefiningSection.Exports[variable]=values

    if map_as_depenance:
        pobj.DefiningSection.ExportAsDepends.add(variable)
        aa=env.Alias("{0}::alias::{1}::{2}".format(env['PART_SECTION'],env['ALIAS'],variable),values)
        
    # set the create SDK value
    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk=False;
        
    if create_sdk:
        pobj._create_sdk_data.append(('ExportItem',[variable,values,False,map_as_depenance]))
        
    errors.ResetPartStackFrameInfo()

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object

SConsEnvironment.ExportCPPPATH=ExportCPPPATH
SConsEnvironment.ExportCPPDEFINES=ExportCPPDEFINES
SConsEnvironment.ExportCFLAGS=ExportCFLAGS
SConsEnvironment.ExportCCFLAGS=ExportCCFLAGS
SConsEnvironment.ExportCXXFLAGS=ExportCXXFLAGS
SConsEnvironment.ExportLINKFLAGS=ExportLINKFLAGS
SConsEnvironment.ExportLIBS=ExportLIBS
SConsEnvironment.ExportItem=ExportItem


