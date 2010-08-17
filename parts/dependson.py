
import version
import common
import functors
import reporter
import SCons.Script 

class REQ:
    # so the idea of the flags are two bits per type
    # 000000
    # llpphh where l is libs, p is libpath, and h is header path
    # also high bit of pair is export to dependent component
    # and low bit of pair is add to the part
    
    
    # these are value to help with the impl.. not for the users
    #This is just a hack to get around the internal backward compatiblity issue
    
    _CPPPATH_IMPORT=0x0001     #0000 0000 0000 0001
    _CPPPATH_EXPORT=0x0002     #0000 0000 0000 0010
    _LIBPATH_IMPORT=0x0004     #0000 0000 0000 0100
    _LIBPATH_EXPORT=0x0008     #0000 0000 0000 1000
    _LIBS_IMPORT=0x0010        #0000 0000 0001 0000
    _LIBS_EXPORT=0x0020        #0000 0000 0010 0000
    _LINKFLAGS_IMPORT=0x0040   #0000 0000 0100 0000
    _LINKFLAGS_EXPORT=0x0080   #0000 0000 1000 0000
    _CCFLAGS_IMPORT=0x0100     #0000 0001 0000 0000
    _CCFLAGS_EXPORT=0x0200     #0000 0010 0000 0000
    _CFLAGS_IMPORT=0x0400      #0000 0100 0000 0000
    _CFLAGS_EXPORT=0x0800      #0000 1000 0000 0000
    _CXXFLAGS_IMPORT=0x1000    #0001 0000 0000 0000
    _CXXFLAGS_EXPORT=0x2000    #0010 0000 0000 0000
    _CPPDEFINES_IMPORT=0x4000  #0100 0000 0000 0000
    _CPPDEFINES_EXPORT=0x8000  #1000 0000 0000 0000
    
    _ALL_DEFAULT=0XFFFFF
    # remove... before release
    
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
    CPPPATH=            _CPPPATH_IMPORT|_CPPPATH_EXPORT
    CPPPATH_INTERNAL=   _CPPPATH_IMPORT
    HEADERS=            _CPPDEFINES_IMPORT|_CPPDEFINES_EXPORT|_CPPPATH_IMPORT|_CPPPATH_EXPORT
    HEADERS_INTERNAL=   _CPPDEFINES_IMPORT|_CPPPATH_IMPORT
    LIBPATH=            _LIBPATH_IMPORT|_LIBPATH_EXPORT
    LIBPATH_INTERNAL=   _LIBPATH_IMPORT
    LIBS=               _LIBPATH_IMPORT|_LIBPATH_EXPORT|_LIBS_IMPORT|_LIBS_EXPORT
    LIBS_INTERNAL=      _LIBPATH_IMPORT|_LIBS_IMPORT

    
    LINKFLAGS_INTERNAL= _LINKFLAGS_IMPORT
    CCFLAGS_INTERNAL=   _CCFLAGS_IMPORT
    CFLAGS_INTERNAL=    _CFLAGS_IMPORT
    CXXFLAGS_INTERNAL=  _CXXFLAGS_IMPORT
    CPPDEFINES=         _CPPDEFINES_IMPORT|_CPPDEFINES_EXPORT
    CPPDEFINES_INTERNAL=_CPPDEFINES_IMPORT
    
    DEFAULT=            HEADERS|LIBS 
    DEFAULT_INTERNAL=   HEADERS_INTERNAL|LIBS_INTERNAL


class ComponentRef:
    def __init__(self,name,version_range='*',requires=REQ.DEFAULT,target_platform=None,local_space=None):
        reporter.SetPartStackFrameInfo()
        self.name=name
        self.version=version.version_range(version_range)
        self.requires=requires
        self.stackframe=reporter.GetPartStackFrameInfo()
        reporter.ResetPartStackFrameInfo()
        self.target=target_platform
        self.local_space=local_space
    
    @property
    def part(self):
        try:
            return self.__part
        except AttributeError:
            self.__part=common.g_engine._part_manager._from_nvp(
                self.name,
                self.version,
                self.target,
                self.local_space
            )
        return self.__part
            
            
    def alias_mapping_string(self):
        return "${PARTID('"+self.name+"','"+str(self.version)+"','alias',True)}"
    
    def resolve_alias(self,env):
        common.g_part_frame.insert(0,self.stackframe)
        tmp = env.subst(self.alias_mapping_string())
        common.g_part_frame.pop(0)
        if tmp=='':
            return None
        return tmp
    

def Component(env,name,version_range='*',requires=REQ.DEFAULT):
    return ComponentRef(name,version_range,requires)


def depends_on_classic(env,depends):
    '''
    This form requires that all dependance get defined by a "mapper" object. 
    This allow for delay processing that is required as at any given time this
    is call we don't really know all the Parts object that could exist. So we leave
    a "calling" card for what we want to find in this place.
    '''
    reporter.SetPartStackFrameInfo()
    pobj=common.g_engine._part_manager._from_env(env)
    if pobj is None:
        return

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
    
    
    for comp in depends:
        # quick error check
        if pobj.Name==comp.name:
            reporter.report_warning("Part depends on with itself")
            reporter.print_msg("Skipping the definition of dependence to SCons")            
            continue
        
        # map what we want to import to this component
        if (comp.requires & REQ._CPPPATH_IMPORT):
            cpppath=common.append_unique(cpppath,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CPPPATH',True)}")
        if (comp.requires & REQ._LIBPATH_IMPORT):
            libpath=common.append_unique(libpath,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','LIBPATH',True)}")
        if (comp.requires & REQ._LIBS_IMPORT):
            libs=common.append_unique(libs,"${PARTLIB('"+comp.name+"','"+str(comp.version)+"','LIBS',True)}")
        if (comp.requires & REQ._LINKFLAGS_IMPORT):
            linkflags=common.append_unique(linkflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','LINKFLAGS',True)}")
        if (comp.requires & REQ._CCFLAGS_IMPORT):
            ccflags=common.append_unique(ccflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CCFLAGS',True)}")
        if (comp.requires & REQ._CFLAGS_IMPORT):
            cflags=common.append_unique(cflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CFLAGS',True)}")
        if (comp.requires & REQ._CXXFLAGS_IMPORT):
            cxxflags=common.append_unique(cxxflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CXXFLAGS',True)}")
        if (comp.requires & REQ._CPPDEFINES_IMPORT):
            cppdefines=common.append_unique(cppdefines,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CPPDEFINES',True)}")
        
        
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
    
    for comp in depends:
        
        if (comp.requires & REQ._CPPPATH_EXPORT):
            cpppath=common.append_unique(cpppath,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CPPPATH',True)}")
        if (comp.requires & REQ._LIBPATH_EXPORT):
            libpath=common.append_unique(libpath,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','LIBPATH',True)}")
        if (comp.requires & REQ._LIBS_EXPORT):
            libs=common.append_unique(libs,"${PARTLIB('"+comp.name+"','"+str(comp.version)+"','LIBS',True)}")
        if (comp.requires & REQ._LINKFLAGS_EXPORT):
            linkflags=common.append_unique(linkflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','LINKFLAGS',True)}")
        if (comp.requires & REQ._CCFLAGS_EXPORT):
            ccflags=common.append_unique(ccflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CCFLAGS',True)}")
        if (comp.requires & REQ._CFLAGS_EXPORT):
            cflags=common.append_unique(cflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CFLAGS',True)}")
        if (comp.requires & REQ._CXXFLAGS_EXPORT):
            cxxflags=common.append_unique(cxxflags,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CXXFLAGS',True)}")
        if (comp.requires & REQ._CPPDEFINES_EXPORT):
            cppdefines=common.append_unique(cppdefines,"${PARTIDEXPORTS('"+comp.name+"','"+str(comp.version)+"','CPPDEFINES',True)}")
    
    # safety check to make sure key exist in the correct form
    if cpppath != []:
        if 'CPPPATH' not in pobj._exports:
            pobj._exports['CPPPATH']=[]
        pobj._exports['CPPPATH']=common.extend_unique(pobj._exports['CPPPATH'],cpppath)
    
    if libpath != []:
        if 'LIBPATH' not in pobj._exports:
            pobj._exports['LIBPATH']=[]
        pobj._exports['LIBPATH']=common.extend_unique(pobj._exports['LIBPATH'],libpath)
    
    if libs != []:
        if 'LIBS' not in pobj._exports:
            pobj._exports['LIBS']=[]
        pobj._exports['LIBS']=common.extend_unique(pobj._exports['LIBS'],libs)
    
    if linkflags != []:
        if 'LINKFLAGS' not in pobj._exports:
            pobj._exports['LINKFLAGS']=[]
        pobj._exports['LINKFLAGS']=common.extend_unique(pobj._exports['LINKFLAGS'],linkflags)
    
    if cflags != []:
        if 'CFLAGS' not in pobj._exports:
            pobj._exports['CFLAGS']=[]
        pobj._exports['CFLAGS']=common.extend_unique(pobj._exports['CFLAGS'],cflags)
    
    if ccflags != []:
        if 'CCFLAGS' not in pobj._exports:
            pobj._exports['CCFLAGS']=[]
        pobj._exports['CCFLAGS']=common.extend_unique(pobj._exports['CCFLAGS'],ccflags)
    
    if cxxflags != []:
        if 'CXXFLAGS' not in pobj._exports:
            pobj._exports['CXXFLAGS']=[]
        pobj._exports['CXXFLAGS']=common.extend_unique(pobj._exports['CXXFLAGS'],cxxflags)
    
    if cppdefines != []:
        if 'CPPDEFINES' not in pobj._exports:
            pobj._exports['CPPDEFINES']=[]
        pobj._exports['CPPDEFINES']=common.extend_unique(pobj._exports['CPPDEFINES'],cppdefines)

    #map up rpath with this.. ( need to fix up the Mac)
    if env['HOST_PLATFORM']!='win32' and env['HOST_PLATFORM'] != 'darwin':
        def_env=common.g_engine
        common.g_engine.add_preprocess_logic_queue(functors.map_rpath_part(env))
        common.g_engine.add_preprocess_logic_queue(functors.map_rpath_link_part(env))
    
    reporter.ResetPartStackFrameInfo()
    
def depends_on(env,depends):
    
    pobj=common.g_engine._part_manager._from_env(env)
    if pobj is None:
        print "fill me in"
        return

    depends_list=[]
    # make this a list if it is not already
    if common.is_list(depends) ==False:
        depends=[depends]
        
    # make any string a component object
    for i in depends:
        if common.is_string(i):
            depends_list.append(Component(i))
        else:
            depends_list.append(i)
            
    # set the target platform in case we want to acces the part object this 
    # would produce latter
    for i in depends_list:    
        i.target=env['TARGET_PLATFORM']
        i.local_space=pobj._uses
        
    # set what we depend on
    # this will be resolved latter when we process the Parts objects
    
    pobj._set_depends(depends_list)
    
    # if this is classic case we will want to resolve now.
    if pobj._is_classic_format:
        # do classic mapper connections to get data where we needed it
        depends_on_classic(env,depends_list)   
    
    
    

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.DependsOn=depends_on
SConsEnvironment.Component=Component
# allow us to add component to parts as a global objects
common.add_parts_object('Component',ComponentRef)   
common.add_parts_object('REQ',REQ)   
