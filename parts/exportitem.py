import os
import re
import SCons.Script
import pattern
import common
import reporter
 
class EXPORT_TYPES:
    FILE=1
    PATH=2
    PATH_FILE=3


def export_path(env,target_dirs,source_dirs,pinfo,prop,use_src=False,create_sdk=True):
    
    # We have three case basicaly of type of paths we pass
    # 1) is the SDK/final path for the file
    # 2) is the build path for the file
    # 3) is the source pasth of the file
    ret=[]
    tmp=pinfo[prop]
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
                
    #pinfo[prop].extend(ret)
    return ret

_reg=re.compile('[\w\-\.]*.so.([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)', re.I)
             
def export_file(env,targets,pinfo,prop):
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
            # ass doing this would upset the linker
            continue
        elif file.endswith('.so-gz'):
            file = file[:-6]
        pinfo[prop]=[file]+pinfo[prop]
    return ret

def export_file_path(env,targets,pinfo,prop,use_src):
    ret=[]
    for t in targets:
        if common.is_string(t):
            t=env.File(t)
        build_path=t.abspath
        final_path=t.srcnode().abspath
        ret.append(final_path)
        if use_src==False:
            # use build directory
            if build_path not in pinfo[prop]:
                pinfo[prop].append(build_path)
        elif final_path not in pinfo[prop]:
                pinfo[prop].append(final_path)
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

def ExportItem(env,prop,values,create_sdk=True):
    reporter.SetPartStackFrameInfo(True)
    def_env=SCons.Script.DefaultEnvironment()
    define_part=def_env.get('DEFINING_PART',None)
    pinfo=def_env['PART_INFO'][define_part]
    
    # set the create SDK value
    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk=False;
    
    if pinfo.has_key(prop)==False:
        pinfo[prop]=[]
    if common.is_list(values)==False:
        values=[values]
    values=SCons.Script.Flatten(values)
   
    for v in values:
        v=str(v)
        if v not in pinfo[prop]:
            pinfo[prop].append(v)
    if create_sdk:
        if pinfo.has_key('CREATE_SDK') == False:
            pinfo['CREATE_SDK']=[]
        pinfo['CREATE_SDK'].append(('ExportItem',[prop,values,False]))
    reporter.ResetPartStackFrameInfo()

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


