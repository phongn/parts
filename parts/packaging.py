import common
import SCons.Script


g_package_groups={}

def PackageGroups():
    return g_package_groups.keys()

def PackageGroup(name,parts=[]):
    '''
    Currently is bound to only handling Parts or Componnet objects ( as these
    allow to refer to a certain Part) The idea of allowing the addition of Files
    or Dir ( and like items) are not being handled at this time as we really
    don't know where we want to put the files in the package.
    '''
    tmp=[]
    parts=common.make_list(parts)
    if g_package_groups.has_key(name) == False:
        g_package_groups[name]=[]
    if parts != [] and name is not None:
        for p in parts:
            #if isinstance(p,Part_t) or isinstance(p,Component):
            #    common.append_unique(tmp,p)
            #elif common.is_string(p):
            if common.is_string(p):
                # test that this is a valid part name or alias
                #if valid:
                    common.append_unique(tmp,p)
            else:
                raise RuntimeError("%s does not refer to a defined Part" % (p) )
            
        g_package_groups[name].extend(tmp)        
        #cache is out of date.. zap it to force rebuild
        if common._INSTALLED_PACKAGING_GROUPS.has_key(name):
            common._INSTALLED_PACKAGING_GROUPS={}
            common._INSTALLED_NO_PACKAGING_GROUPS={}
            
    return g_package_groups[name]

def ReplacePackageGroupFilter(env,name,func):
    env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)

def AppendMapPackageGroupFilter(env,name,func):
    try:
        env['PACKAGE_GROUP_FILTER'][name].extend(common.make_list(func))
    except:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
        
def PrependMapPackageGroupFilter(env,name,func):
    try:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)+env['MAP_PACKAGE_GROUP'][name]
    except:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)

def get_part_alias(obj):
    #if isinstance(obj,Component):
        #return obj.resolve_alias()
    return obj

def GetPackageGroupFiles(name,no_pkg=False):
    '''
    Get all the file that are installed that are define as part of a group.
    This function will try to cache known result to improve speed.
    '''
    
    try:
        return (no_pkg and common._INSTALLED_NO_PACKAGING_GROUPS[name] or common._INSTALLED_PACKAGING_GROUPS[name])
    except KeyError:
        
        SortPackageGroups()
                    
    return (no_pkg and common._INSTALLED_NO_PACKAGING_GROUPS.get(name,[]) or common._INSTALLED_PACKAGING_GROUPS.get(name,[]))

def SortPackageGroups():

    grps=PackageGroups() # get the groups
    def_env=SCons.Script.DefaultEnvironment() #get reference to default environment
    
    for name in grps:
        #get the component that are part of the group
        obj_lst=PackageGroup(name)
        # reset the cache for this name
        common._INSTALLED_PACKAGING_GROUPS={}
        common._INSTALLED_NO_PACKAGING_GROUPS={}
        
        for obj in obj_lst:
            if isinstance(obj,SCons.Node.FS.File):
                files=[obj]
                map_objs=def_env.get('PACKAGE_GROUP_FILTER',[])
                env=def_env
            else: # assume this is a part
                pinfo=def_env['PART_INFO'][get_part_alias(obj)]
                env=pinfo['ENV']
                map_objs=env.get('MAP_PACKAGE_GROUP',[])
                files=pinfo['INSTALLED_FILES']
            for f in files:
                _no_pkg=def_env.MetaTagValue(f,'no_package','package',False)
                group_val=env.MetaTagValue(f,'group','package',None)
                if group_val is None:
                    group_val=name
                    #apply meta tag to file
                    env.MetaTag(f,'package',group=group_val)
                    #apply any mappings
                    for tmp in map_objs:
                        key,tests=tmp
                        for t in tests:
                            if t(f):
                                env.MetaTag(f,'package',group=key)
                                break
                                
                if _no_pkg==False:
                    try:
                        common._INSTALLED_PACKAGING_GROUPS[group_val].append(f)
                    except KeyError:
                        common._INSTALLED_PACKAGING_GROUPS[group_val]=[f]
                        common._INSTALLED_NO_PACKAGING_GROUPS[group_val]=[]
                else:
                    try:
                        common._INSTALLED_NO_PACKAGING_GROUPS[group_val].append(f)
                    except KeyError:
                        common._INSTALLED_PACKAGING_GROUPS[group_val]=[]
                        common._INSTALLED_NO_PACKAGING_GROUPS[group_val]=[f]
                    





def GetPackageGroupFiles_env(env,name,no_pkg=False):
    return GetPackageGroupFiles(name,no_pkg)
    
from SCons.Script.SConscript import SConsEnvironment


SConsEnvironment.GetPackageGroupFiles=GetPackageGroupFiles_env
    
common.add_global_value('PackageGroups',PackageGroups)   
common.add_global_value('PackageGroup',PackageGroup)   
common.add_global_value('GetPackageGroupFiles',GetPackageGroupFiles)   

