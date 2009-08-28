
import parts.version as version
import parts.common as common
import parts.functors as functors
import SCons.Script 

class REQ:
    # so the idea of the flags are two bits per type
    # 000000
    # llpphh where l is libs, p is libpath, and h is header path
    # also high bit of pair is export to dependent component
    # and low bit of pair is add to the part
    
    
    # these are value to help with the impl.. not for the users
    #This is just a hack to get around the internal backward compatiblity issue
    
    CPPPATH_IMPORT=0x0001     #0000 0000 0000 0001
    CPPPATH_EXPORT=0x0002     #0000 0000 0000 0010
    LIBPATH_IMPORT=0x0004     #0000 0000 0000 0100
    LIBPATH_EXPORT=0x0008     #0000 0000 0000 1000
    LIBS_IMPORT=0x0010        #0000 0000 0001 0000
    LIBS_EXPORT=0x0020        #0000 0000 0010 0000
    LINKFLAGS_IMPORT=0x0040   #0000 0000 0100 0000
    LINKFLAGS_EXPORT=0x0080   #0000 0000 1000 0000
    CCFLAGS_IMPORT=0x0100     #0000 0001 0000 0000
    CCFLAGS_EXPORT=0x0200     #0000 0010 0000 0000
    CFLAGS_IMPORT=0x0400      #0000 0100 0000 0000
    CFLAGS_EXPORT=0x0800      #0000 1000 0000 0000
    CXXFLAGS_IMPORT=0x1000    #0001 0000 0000 0000
    CXXFLAGS_EXPORT=0x2000    #0010 0000 0000 0000
    CPPDEFINES_IMPORT=0x4000  #0100 0000 0000 0000
    CPPDEFINES_EXPORT=0x8000  #1000 0000 0000 0000
    
    ALL_DEFAULT=0XFFFFF
    
    ## these are external use
    
    # we make value based on headers, libpath and libs. in the case of lib we 
    # assume you also want the libpath in the same fashion
    EXISTS= 0                   #0000 0000 0000 0000
    CPPPATH=            CPPPATH_IMPORT|CPPPATH_EXPORT
    CPPPATH_INTERNAL=   CPPPATH_IMPORT
    HEADERS=            CPPDEFINES_IMPORT|CPPDEFINES_EXPORT|CPPPATH_IMPORT|CPPPATH_EXPORT
    HEADERS_INTERNAL=   CPPDEFINES_IMPORT|CPPPATH_IMPORT
    LIBPATH=            LIBPATH_IMPORT|LIBPATH_EXPORT
    LIBPATH_INTERNAL=   LIBPATH_IMPORT
    LIBS=               LIBPATH_IMPORT|LIBPATH_EXPORT|LIBS_IMPORT|LIBS_EXPORT
    LIBS_INTERNAL=      LIBPATH_IMPORT|LIBS_IMPORT

    
    LINKFLAGS_INTERNAL= LINKFLAGS_IMPORT
    CCFLAGS_INTERNAL=   CCFLAGS_IMPORT
    CFLAGS_INTERNAL=    CFLAGS_IMPORT
    CXXFLAGS_INTERNAL=  CXXFLAGS_IMPORT
    CPPDEFINES=         CPPDEFINES_IMPORT|CPPDEFINES_EXPORT
    CPPDEFINES_INTERNAL=CPPDEFINES_IMPORT
    
    DEFAULT=            HEADERS|LIBS 
    DEFAULT_INTERNAL=   HEADERS_INTERNAL|LIBS_INTERNAL


class ComponentRef:
    def __init__(self,name,version_range='*',requires=REQ.ALL_DEFAULT,internal=-1):
        self.name=name
        self.version=version.version_range(version_range)
        self.requires=requires
            
    def alias_mapping_string(self):
        return "${PARTID('"+self.name+"','"+str(self.version)+"','ALIAS')}"
    
    def resolve_alias(self,env):
        return env.subst(self.alias_mapping_string())

def Component(env,name,version_range='*',requires=REQ.ALL_DEFAULT):
    return ComponentRef(name,version_range,requires)


def depends_on(env,depends):
    def_env=SCons.Script.DefaultEnvironment()
    rpt=def_env['PARTS_REPORTER']
    alias=def_env['DEFINING_PART']
    if alias == None:
        return
    
    pinfo=def_env['PART_INFO'][alias]
    
    # depends that get passed on
    if common.is_list(depends) ==False:
        depends=[depends]
    
    cpppath=[]
    libpath=[]
    libs=[]
    cppdefines=[]
    linkflags=[]
    ccflags=[]
    cflags=[]
    cxxflags=[]
    
    
    for d in depends:
        if common.is_string(d):
            comp=component.component(d)
        else:
            comp=d
        # quick error check
        if pinfo['NAME']==comp.name:
            rpt.part_warning(env,"Part depends on with itself")
            rpt.part_message("Skipping the definition of dependence to Scons")
            #print "Parts: WARNING - Part alias [",alias,"] with name of [",pinfo['NAME'],"] is defined depends on with itself"
            #print "Parts: WARNING - Skipping the definition of dependence to Scons"
            continue
        if (comp.requires & REQ.CPPPATH_IMPORT):
            cpppath.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CPPPATH',True)}")
        if (comp.requires & REQ.LIBPATH_IMPORT):
            libpath.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','LIBPATH',True)}")
        if (comp.requires & REQ.LIBS_IMPORT):
            libs.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','LIBS',True)}")
        if (comp.requires & REQ.LINKFLAGS_IMPORT):
            linkflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','LINKFLAGS',True)}")
        if (comp.requires & REQ.CCFLAGS_IMPORT):
            ccflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CCFLAGS',True)}")
        if (comp.requires & REQ.CFLAGS_IMPORT):
            cflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CFLAGS',True)}")
        if (comp.requires & REQ.CXXFLAGS_IMPORT):
            cxxflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CXXFLAGS',True)}")
        if (comp.requires & REQ.CPPDEFINES_IMPORT):
            cppdefines.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CPPDEFINES',True)}")
        
        #unknown_alias=comp.alias_mapping_string()
        #def_env['PREPROCESS_LOGIC_QUEUE'].append(functors.map_parts_alias(env,unknown_alias))
        #pinfo['DEPENDSON'].append(unknown_alias)
        pinfo['DEPENDSON'].append(comp)
        
    #add the dependent info
    env.Append(
        CPPPATH=cpppath,LIBPATH=libpath,LIBS=libs,CPPDEFINES=cppdefines,
        LINKFLAGS=linkflags,CCFLAGS=ccflags,CFLAGS=cflags,CXXFLAGS=cxxflags
        )
            
    cpppath=[]
    libpath=[]
    libs=[]
    cppdefines=[]
    libflags=[]
    ccflags=[]
    cflags=[]
    cxxflags=[]
    
    for d in depends:
        if common.is_string(d):
            comp=component.component(d)
        else:
            comp=d
        
        if (comp.requires & REQ.CPPPATH_EXPORT):
            cpppath.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CPPPATH',True)}")
        if (comp.requires & REQ.LIBPATH_EXPORT):
            libpath.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','LIBPATH',True)}")
        if (comp.requires & REQ.LIBS_EXPORT):
            libs.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','LIBS',True)}")
        if (comp.requires & REQ.LINKFLAGS_EXPORT):
            linkflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','LINKFLAGS',True)}")
        if (comp.requires & REQ.CCFLAGS_EXPORT):
            ccflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CCFLAGS',True)}")
        if (comp.requires & REQ.CFLAGS_EXPORT):
            cflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CFLAGS',True)}")
        if (comp.requires & REQ.CXXFLAGS_EXPORT):
            cxxflags.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CXXFLAGS',True)}")
        if (comp.requires & REQ.CPPDEFINES_EXPORT):
            cppdefines.append("${PARTID('"+comp.name+"','"+str(comp.version)+"','CPPDEFINES',True)}")
        
    # safety check to make sure key exist in the correct form
    if 'CPPPATH' not in pinfo:
        pinfo['CPPPATH']=[]
    if 'LIBPATH' not in pinfo:
        pinfo['LIBPATH']=[]
    if 'LIBS' not in pinfo:
        pinfo['LIBS']=[]
    if 'LINKFLAGS' not in pinfo:
        pinfo['LINKFLAGS']=[]
    if 'CFLAGS' not in pinfo:
        pinfo['CFLAGS']=[]
    if 'CCFLAGS' not in pinfo:
        pinfo['CCFLAGS']=[]
    if 'CXXFLAGS' not in pinfo:
        pinfo['CXXFLAGS']=[]
    if 'CPPDEFINES' not in pinfo:
        pinfo['CPPDEFINES']=[]
    
    # add the values...
    pinfo['CPPPATH'].extend(cpppath)
    pinfo['LIBPATH'].extend(libpath)
    pinfo['LIBS'].extend(libs)
    pinfo['LINKFLAGS'].extend(linkflags)
    pinfo['CFLAGS'].extend(cflags)
    pinfo['CCFLAGS'].extend(ccflags)
    pinfo['CXXFLAGS'].extend(cxxflags)
    pinfo['CPPDEFINES'].extend(cppdefines)
    
    #map up rpath with this.. ( need to fix up the Mac)
    if def_env['PLATFORM']!='win32' and def_env['PLATFORM'] != 'darwin':
        def_env['PREPROCESS_LOGIC_QUEUE'].append(functors.map_rpath_part(env))
        def_env['PREPROCESS_LOGIC_QUEUE'].append(functors.map_rpath_link_part(env))
        

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.DependsOn=depends_on
SConsEnvironment.Component=Component
# allow us to add component to parts as a global objects
common.add_parts_object('Component',ComponentRef)   
common.add_parts_object('REQ',REQ)   
