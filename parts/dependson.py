
from requirement import REQ
import version
import common
import functors
import reporter
import SCons.Script 


class ComponentRef(object):
    def __init__(self,name,version_range,requires=REQ.DEFAULT,target_platform=None,local_space=None):
        reporter.SetPartStackFrameInfo()
        self.name=name
        self.version=version.version_range(version_range)
        self.requires=REQ()|requires

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
    

def Component(env,name,version_range=None,requires=REQ.DEFAULT):
    localspace=None
    if version_range is None:
        # get pobj
        pobj= common.g_engine._part_manager._from_env(env)
        localspace=pobj._uses
        if pobj.Root.Name==name.split('.')[0]:
            version_range=pobj.Version
        else:
            version_range='*'
    return ComponentRef(name,version_range,requires,local_space=localspace)

class ComponentEnv(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,name,version_range=None,requires=REQ.DEFAULT):
        return self.env.Component(name,version_range,requires)

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
    reporter.verbose_msg('dependson', "Mapping data to Part",pobj.Name)
    # depends that get passed on
    if common.is_list(depends) ==False:
        depends=[depends]
    
    for comp in depends:
        # quick error check
        if pobj.Name==comp.name:
            reporter.report_warning("Part depends on with itself")
            reporter.print_msg("Skipping the definition of dependence to SCons")            
            continue
        reporter.verbose_msg('dependson'," Component",comp.name,comp.version)
        import_map={}
        for r in comp.requires:
            ## import logic
            # always map to namespace
            ## split the name so we can make an sub spaces            
            tmp=comp.name.split('.')
            # get the space in the environment
            try:
                tmpspace=env['DEPENDS']
            except KeyError:
                tmpspace=common.namespace()
                env['DEPENDS']=tmpspace
                
            for i in tmp:
                try:
                    tmpspace=tmpspace[i]
                except KeyError:
                    tmpspace[i]=common.namespace()
                    tmpspace=tmpspace[i]
            
            tmpspace[r.key]=r.value_mapper(comp.name,comp.version,r.key)
            
            # if this is a list and is not private we map to global space via an append
            if r.is_public and r.is_list:
                env.AppendUnique(
                    delete_existing=True,
                    **{r.key:[r.value_mapper(comp.name,comp.version,r.key)]}
                    )
                    
            elif r.is_public:
                if env.has_key(r.key):
                    env[r.key]=[env[r.key],r.value_mapper(comp.name,comp.version,r.key)]
                else:
                    env[r.key]=r.value_mapper(comp.name,comp.version,r.key)
            ##export logic
            # if this is not internal we add to the current component export table        
            if r.is_internal == False:
                reporter.verbose_msg('dependson', "  exporting",r.key,r.value_mapper(comp.name,comp.version,r.key))
                if r.key not in pobj._exports and r.is_list:
                    pobj._exports[r.key]=[]
                    
                if r.is_list: 
                    pobj._exports[r.key]=common.extend_unique(pobj._exports[r.key],[r.value_mapper(comp.name,comp.version,r.key)])
                else:
                    if pobj._exports.has_key(r.key):
                        pobj._exports[r.key]=[pobj._exports[r.key],r.value_mapper(comp.name,comp.version,r.key)]
                    else:
                        pobj._exports[r.key]=r.value_mapper(comp.name,comp.version,r.key)
                

   
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
common.add_parts_object('Component',ComponentEnv,True)   
common.add_parts_object('REQ',REQ)   
