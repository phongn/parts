import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil, os
import operator,platform

def rpm_wrapper_mapper(env, target, sources, **kw):
    def rpm_builder():

        #############################################
        # getting all the sources
        new_sources, _ = env.Override(kw).GetFilesFromPackageGroups(target, sources)

        #############################################
        ## Sort files in to source group and to control group
        def spec(node):
            if env.MetaTagValue(node, 'category', 'package')=='PKGDATA':
                if 'rpm' in env.MetaTagValue(node, 'types', 'package', ['rpm']):
                    env.CCopy('${{BUILD_DIR}}/SPECS/{0}'.format(target[0].name[:-4]),node)
                return False
            return True

        src=filter(spec,new_sources)

        #############################################
        ##create the source gz file
        #Replace source with the name and version  from the specfile for proper formatting of build of the tar.gz file
        #and building the rpm 
        env._rpmspec(target, src,**kw)
    return rpm_builder

def RpmPackage_wrapper(_env, target, sources, **kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better
    # clone the KWS to the env to change the filename

    env=_env.Clone(**kw)
    env['NAME']  = kw['NAME']
    env['VERSION'] = kw['VERSION']
    env['RELEASE'] = kw['RELEASE']

    #Mapping for the target architecture with dictionary of known architectures
    #depending on the $TARGET_ARCH
    def rpmarch(target_arch):
        arch_map_rpm = {}
        arch_map_rpm.update(glb.arch_map)
        arch_mapper = dict(env['PKG_ARCH_MAPPER'].items()+env.get('arch_mapper',{}).items())

        def implicit_rpm_mapping(target_arch):
            rpm_arch=None
            if not arch_mapper:
                rpm_arch = platform.machine()
            arch_map_rpm[target_arch]=rpm_arch
            return rpm_arch
        
        def explicit_rpm_mapping(target_arch):
            rpm_arch=None
            if arch_map_rpm.has_key(target_arch):
                     rpm_arch = arch_mapper[target_arch]
                     arch_map_rpm[target_arch]=rpm_arch
            return rpm_arch

        try:
            #explicit mapping: when the given architecture maps to arch_map_rpm for the system
            # it uses the corresponding value for target_arch
            # else if the key is not in arch_map_rpm (glb.arch_map), it maps to the new value
            if target_arch == arch_mapper[target_arch]:
                if arch_map_rpm.get(target_arch)==arch_mapper.get(target_arch): 
                   new_target_arch = target_arch

            elif arch_map_rpm.has_key(target_arch):
                 if arch_mapper.get(target_arch) is not None: 
                    arch_map_rpm[target_arch]=explicit_rpm_mapping(target_arch)
                    new_target_arch = arch_map_rpm[target_arch]

        except KeyError:
                #implicit mapping: when the given architecture is none,
                # the key maps to the platform system architecture
                arch_map_rpm[target_arch]=implicit_rpm_mapping(target_arch)
                new_target_arch = arch_map_rpm[target_arch]
        return new_target_arch

    target_arch = env['TARGET_ARCH']

    expected_target_arch = kw.get(target_arch, rpmarch(target_arch))
    env['TARGET_ARCH'] = expected_target_arch
 
    target = env.arg2nodes(target,env.fs.File) #common.make_list(target)
    sources= common.make_list(sources) 

    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')

    fname = env.subst(target[0].name)

    if str(fname).endswith('.rpm'):
        target=[env.Dir("_rpm/{0}".format(fname[:-4])).File(fname)]
    else:
        target=[env.Dir("_rpm/{0}".format(fname[:-4])).File(fname+".rpm")]

    # subst all source values to get finial package group names
    sources=[env.subst(s) for s in sources]

    # delay real work till we have everything loaded
    glb.engine.add_preprocess_logic_queue(rpm_wrapper_mapper(env, target, sources, **kw))

    return target

api.register.add_variable('PKG_ARCH_MAPPER',{},'')

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.RPMPackage=RpmPackage_wrapper
