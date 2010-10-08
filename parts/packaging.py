import common
import SCons.Script
import reporter
import metatag

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
    name=SCons.Script.DefaultEnvironment().subst(name)
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

# global form
def ReplacePackageGroupCriteria(name,func):
    name=SCons.Script.DefaultEnvironment().subst(name)
    common.g_defaultoverides['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)

def AppendPackageGroupCriteria(name,func):
    name=SCons.Script.DefaultEnvironment().subst(name)
    try:
        common.g_defaultoverides['PACKAGE_GROUP_FILTER'][name].extend(common.make_list(func))
    except:
        common.g_defaultoverides['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)
        
def PrependPackageGroupCriteria(name,func):
    name=SCons.Script.DefaultEnvironment().subst(name)
    try:
        common.g_defaultoverides['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)+common.g_defaultoverides['MAP_PACKAGE_GROUP'][name]
    except:
        common.g_defaultoverides['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)



# env form
def ReplacePackageGroupCriteriaEnv(env,name,func):
    name=env.subst(name)
    env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)

def AppendPackageGroupCriteriaEnv(env,name,func):
    name=env.subst(name)
    try:
        env['PACKAGE_GROUP_FILTER'][name].extend(common.make_list(func))
    except:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)
        
def PrependPackageGroupCriteriaEnv(env,name,func):
    name=env.subst(name)
    try:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)+env['MAP_PACKAGE_GROUP'][name]
    except:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)

def get_part_alias(obj):
    #if isinstance(obj,Component):
        #return obj.resolve_alias()
    return obj

def GetPackageGroupFiles(name,no_pkg=False):
    '''
    Get all the file that are installed that are define as part of a group.
    This function will try to cache known result to improve speed.
    '''
    # get Cache value
    try:
        return (no_pkg and common._INSTALLED_NO_PACKAGING_GROUPS[name] or common._INSTALLED_PACKAGING_GROUPS[name])
    except KeyError:
        # no cache value.. re build list
        SortPackageGroups()  
        
            
    # return what we got, if not in rebuilt list return empty list
    return (no_pkg and common._INSTALLED_NO_PACKAGING_GROUPS.get(name,[]) or common._INSTALLED_PACKAGING_GROUPS.get(name,[]))

def SortPackageGroups():

    grps=PackageGroups() # get the groups
    
    # reset the cache for this name
    common._INSTALLED_PACKAGING_GROUPS={}
    common._INSTALLED_NO_PACKAGING_GROUPS={}
    for name in grps:
        if common._INSTALLED_PACKAGING_GROUPS.has_key(name)==False:
            common._INSTALLED_PACKAGING_GROUPS[name]=[]
            common._INSTALLED_NO_PACKAGING_GROUPS[name]=[]
        #get the component that are part of the group
        obj_lst=PackageGroup(name)    
        for obj in obj_lst:            
            if isinstance(obj,SCons.Node.FS.File):
                files=[obj]
                map_objs=common.g_engine.def_env.get('PACKAGE_GROUP_FILTER',[])
            else: # assume this is a part
                pobj=common.g_engine._part_manager._from_alias(obj)
                map_objs=pobj.Env.get('PACKAGE_GROUP_FILTER',[])
                files=pobj._installed_files
                
            for f in files:
                _no_pkg=metatag.MetaTagValue(f,'no_package','package',False)
                group_val=metatag.MetaTagValue(f,'group','package',None)
                if group_val is None:
                    group_val=name
                    #apply meta tag to file
                    metatag.MetaTag(f,'package',group=group_val)
                    #apply any mappings
                    
                    for tmp in map_objs.items():
                        key,tests=tmp
                        for t in tests:
                            if t(f):
                                metatag.MetaTag(f,'package',group=key)
                                #get new group value
                                reporter.verbose_msg('packaging',"Remapping",f,"from package_group",group_val,'to',key)
                                group_val=key
                                break
                    
                
                if _no_pkg==False:
                    try:
                        common.append_unique(common._INSTALLED_PACKAGING_GROUPS[group_val],f)
                    except KeyError:
                        common._INSTALLED_PACKAGING_GROUPS[group_val]=[f]
                        common._INSTALLED_NO_PACKAGING_GROUPS[group_val]=[]
                else:
                    try:
                        common.append_unique(common._INSTALLED_NO_PACKAGING_GROUPS[group_val],f)
                    except KeyError:
                        common._INSTALLED_PACKAGING_GROUPS[group_val]=[]
                        common._INSTALLED_NO_PACKAGING_GROUPS[group_val]=[f]

def GetPackageGroupFiles_env(env,name,no_pkg=False):
    return GetPackageGroupFiles(name,no_pkg)

# compatible for mistakes

def ReplacePackageGroupCritera(name,func):
    reporter.report_warning('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return ReplacePackageGroupCriteria(name,func)

def AppendPackageGroupCritera(name,func):
    reporter.report_warning('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return AppendPackageGroupCriteria(name,func)
        
def PrependPackageGroupCritera(name,func):
    reporter.report_warning('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return PrependPackageGroupCriteria(name,func)


def ReplacePackageGroupCriteriaEnv_old(env,name,func):
    reporter.report_warning('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.ReplacePackageGroupCriteria(name,func)
def AppendPackageGroupCriteriaEnv_old(env,name,func):
    reporter.report_warning('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.AppendPackageGroupCriteria(name,func)
def PrependPackageGroupCriteriaEnv_old(env,name,func):
    reporter.report_warning('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.PrependPackageGroupCriteria(name,func)
    
    
from SCons.Script.SConscript import SConsEnvironment


SConsEnvironment.GetPackageGroupFiles=GetPackageGroupFiles_env

SConsEnvironment.ReplacePackageGroupCritera=ReplacePackageGroupCriteriaEnv_old
SConsEnvironment.AppendPackageGroupCritera=AppendPackageGroupCriteriaEnv_old
SConsEnvironment.PrependPackageGroupCritera=PrependPackageGroupCriteriaEnv_old

SConsEnvironment.ReplacePackageGroupCriteria=ReplacePackageGroupCriteriaEnv
SConsEnvironment.AppendPackageGroupCriteria=AppendPackageGroupCriteriaEnv
SConsEnvironment.PrependPackageGroupCriteria=PrependPackageGroupCriteriaEnv
    
common.add_global_value('PackageGroups',PackageGroups)   
common.add_global_value('PackageGroup',PackageGroup)   
common.add_global_value('GetPackageGroupFiles',GetPackageGroupFiles)   

common.add_global_value('ReplacePackageGroupCritera',ReplacePackageGroupCritera)   
common.add_global_value('AppendPackageGroupCritera',AppendPackageGroupCritera)   
common.add_global_value('PrependPackageGroupCritera',PrependPackageGroupCritera)

common.add_global_value('ReplacePackageGroupCriteria',ReplacePackageGroupCriteria)   
common.add_global_value('AppendPackageGroupCriteria',AppendPackageGroupCriteria)   
common.add_global_value('PrependPackageGroupCriteria',PrependPackageGroupCriteria)   

