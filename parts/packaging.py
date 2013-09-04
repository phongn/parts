import glb
import common
import metatag
import api.output
import settings

import SCons.Script



g_package_groups={}

_packaging_groups = _INSTALLED_PACKAGING_GROUPS, _INSTALLED_NO_PACKAGING_GROUPS = dict(), dict()

def PackageGroups():
    return g_package_groups.keys()

def PackageGroup(name,parts=None):
    '''
    Currently is bound to only handling Parts or Componnet objects ( as these
    allow to refer to a certain Part) The idea of allowing the addition of Files
    or Dir ( and like items) are not being handled at this time as we really
    don't know where we want to put the files in the package.
    '''

    name = SCons.Script.DefaultEnvironment().subst(name)
    if not name:
        return []

    try:
        result = g_package_groups[name]
    except KeyError:
        g_package_groups[name] = result = list()

    if parts:
        parts = common.make_list(parts)
        for p in parts:
            if common.is_string(p):
                common.append_unique(result,p)
                api.output.verbose_msg('packaging','Adding to PackageGroup :"{0}" Part: "{1}"'.format(name,p))
            else:
                raise RuntimeError("%s does not refer to a defined Part" % (p) )

        #cache is out of date.. zap it to force rebuild
        if _INSTALLED_PACKAGING_GROUPS.has_key(name):
            _INSTALLED_PACKAGING_GROUPS.clear()
            _INSTALLED_NO_PACKAGING_GROUPS.clear()

    return result

# global form
def ReplacePackageGroupCriteria(name,func):
    name=SCons.Script.DefaultEnvironment().subst(name)
    settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]=common.make_list(func)
    return PackageGroup(name)

def AppendPackageGroupCriteria(name,func):
    name=SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name].extend(common.make_list(func))
    except:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]=common.make_list(func)
    return PackageGroup(name)

def PrependPackageGroupCriteria(name,func):
    name=SCons.Script.DefaultEnvironment().subst(name)
    try:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]=common.make_list(func)+settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]
    except:
        settings.DefaultSettings().vars['PACKAGE_GROUP_FILTER'].Default[name]=common.make_list(func)
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
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)+env['PACKAGE_GROUP_FILTER'][name]
    except:
        env['PACKAGE_GROUP_FILTER'][name]=common.make_list(func)
    return PackageGroup(name)

def GetPackageGroupFiles(name,no_pkg=False):
    '''
    Get all the file that are installed that are define as part of a group.
    This function will try to cache known result to improve speed.
    '''
    # get Cache value
    if no_pkg:
        groups = _INSTALLED_NO_PACKAGING_GROUPS
    else:
        groups = _INSTALLED_PACKAGING_GROUPS
    try:
        return groups[name]
    except KeyError:
        # no cache value.. re build list
        api.output.verbose_msg('packaging','Sorting PackageGroup Parts into nodes')
        SortPackageGroups()


    # return what we got, if not in rebuilt list return empty list
    return groups.get(name,[])

def get_group_list(name, no_pkg):
    if no_pkg:
        that, this = _packaging_groups
    else:
        this, that = _packaging_groups

    try:
        return this[name]
    except KeyError:
        this[name] = result = list()
        that[name] = list()
        return result

def SortPackageGroups():

    grps=PackageGroups() # get the groups

    # reset the cache
    for group in _packaging_groups:
        group.clear()

    for name in grps:
        #get the component that are part of the group
        obj_lst=PackageGroup(name)
        api.output.verbose_msg('packaging','Sorting Group:',name)
        for obj in obj_lst:
            if isinstance(obj,SCons.Node.FS.File):
                files=[obj]
                map_objs=glb.engine.def_env.get('PACKAGE_GROUP_FILTER',[])
            else: # assume this is a part
                pobj=glb.engine._part_manager._from_alias(obj)
                map_objs=pobj.Env.get('PACKAGE_GROUP_FILTER',[])
                # this needs to be updated with we add teh new format ( and lots of different section types)
                files=pobj.Section('build').InstalledFiles

            for f in files:
                _no_pkg=metatag.MetaTagValue(f,'no_package','package',False)
                group_val=metatag.MetaTagValue(f,'group','package',None)
                if group_val is None:
                    group_val=name
                    #apply meta tag to file
                    metatag.MetaTag(f,'package',group=group_val)
                    #apply any mappings

                    for tmp in map_objs.iteritems():
                        key,tests=tmp
                        for t in tests:
                            if t(f):
                                metatag.MetaTag(f,'package',group=key)
                                #get new group value
                                api.output.verbose_msg('packaging',"Remapping",f,"from package_group",group_val,'to',key)
                                group_val=key
                                break
                common.append_unique(get_group_list(group_val, _no_pkg), f)
                api.output.verbose_msg('packaging','Adding to PackageGroup={0}, no_package={1} nodes={2}'.format(group_val, _no_pkg, f.ID))

def GetPackageGroupFiles_env(env,name,no_pkg=False):
    return GetPackageGroupFiles(name,no_pkg)

# compatible for mistakes

def ReplacePackageGroupCritera(name,func):
    api.output.warning_msg('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return ReplacePackageGroupCriteria(name,func)

def AppendPackageGroupCritera(name,func):
    api.output.warning_msg('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return AppendPackageGroupCriteria(name,func)

def PrependPackageGroupCritera(name,func):
    api.output.warning_msg('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return PrependPackageGroupCriteria(name,func)


def ReplacePackageGroupCriteriaEnv_old(env,name,func):
    api.output.warning_msg('ReplacePackageGroupCritera is deprecated, use ReplacePackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.ReplacePackageGroupCriteria(name,func)
def AppendPackageGroupCriteriaEnv_old(env,name,func):
    api.output.warning_msg('AppendPackageGroupCritera is deprecated, use AppendPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.AppendPackageGroupCriteria(name,func)
def PrependPackageGroupCriteriaEnv_old(env,name,func):
    api.output.warning_msg('PrependPackageGroupCritera is deprecated, use PrependPackageGroupCriteria',"(NOTE: there is an 'i' missing in the word Criteria in the old usage)")
    return env.PrependPackageGroupCriteria(name,func)


from SCons.Script.SConscript import SConsEnvironment


SConsEnvironment.GetPackageGroupFiles=GetPackageGroupFiles_env

SConsEnvironment.ReplacePackageGroupCritera=ReplacePackageGroupCriteriaEnv_old
SConsEnvironment.AppendPackageGroupCritera=AppendPackageGroupCriteriaEnv_old
SConsEnvironment.PrependPackageGroupCritera=PrependPackageGroupCriteriaEnv_old

SConsEnvironment.ReplacePackageGroupCriteria=ReplacePackageGroupCriteriaEnv
SConsEnvironment.AppendPackageGroupCriteria=AppendPackageGroupCriteriaEnv
SConsEnvironment.PrependPackageGroupCriteria=PrependPackageGroupCriteriaEnv

api.register.add_variable('PACKAGE_GROUP_FILTER',{},"")

api.register.add_global_object('PackageGroups',PackageGroups)
api.register.add_global_object('PackageGroup',PackageGroup)
api.register.add_global_object('GetPackageGroupFiles',GetPackageGroupFiles)

api.register.add_global_object('ReplacePackageGroupCritera',ReplacePackageGroupCritera)
api.register.add_global_object('AppendPackageGroupCritera',AppendPackageGroupCritera)
api.register.add_global_object('PrependPackageGroupCritera',PrependPackageGroupCritera)

api.register.add_global_object('ReplacePackageGroupCriteria',ReplacePackageGroupCriteria)
api.register.add_global_object('AppendPackageGroupCriteria',AppendPackageGroupCriteria)
api.register.add_global_object('PrependPackageGroupCriteria',PrependPackageGroupCriteria)

