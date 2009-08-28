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
        try:
            g_package_groups[name].extend(tmp)
        except KeyError:
            g_package_groups[name]=tmp
        #cache is out of date.. zap it to force rebuild
        if common._INSTALLED_PACKAGING_GROUPS.has_key(name):
            del common._INSTALLED_PACKAGING_GROUPS[name]
            del common._INSTALLED_NO_PACKAGING_GROUPS[name]
            
        
    return g_package_groups[name]

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
        
        # see that we have the group defined
        if name not in PackageGroups():
            print "Group Not Found"
            return None
        
        #get the component that are part of the group
        part_lst=PackageGroup(name)
        #if so gather all the installed files for the defined parts that are part 
        # of the group
        common._INSTALLED_PACKAGING_GROUPS[name]=[]
        common._INSTALLED_NO_PACKAGING_GROUPS[name]=[]
        def_env=SCons.Script.DefaultEnvironment()
        for p in part_lst:
            pinfo=def_env['PART_INFO'][get_part_alias(p)]
            files=pinfo['INSTALLED_FILES']
            for f in files:
                _no_pkg=def_env.MetaTagValue(f,'no_package','package',False)
                if _no_pkg==False:
                    common._INSTALLED_PACKAGING_GROUPS[name].append(f)
                else:
                    common._INSTALLED_NO_PACKAGING_GROUPS[name].append(f)
                    
    return (no_pkg and common._INSTALLED_NO_PACKAGING_GROUPS[name] or common._INSTALLED_PACKAGING_GROUPS[name])

def GetPackageGroupFiles_env(env,name,no_pkg=False):
    return GetPackageGroupFiles(name,no_pkg)
    
from SCons.Script.SConscript import SConsEnvironment


SConsEnvironment.GetPackageGroupFiles=GetPackageGroupFiles_env
    
common.add_global_value('PackageGroups',PackageGroups)   
common.add_global_value('PackageGroup',PackageGroup)   
common.add_global_value('GetPackageGroupFiles',GetPackageGroupFiles)   

