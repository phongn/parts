## the core logic

import fnmatch
import shutil
import os
import string
import stat

import SCons.Script 

import pattern
import config
import common 
import version
import mappers
import functors

def parts_version_text():
    import parts_version
    return 'Parts extension for SCons, Version '+parts_version._PARTS_VERSION

def parts_version_text_env(env):
    return parts_version_text()

def is_parts_version_beta():
    import parts_version
    if parts_version._PARTS_VERSION[-4:].lower()=='beta':
        return True
    return False

def is_parts_version_beta_env(env):
    return is_parts_version_beta()

def PartsExtensionVersion():
    import parts_version
    if is_parts_version_beta():
        return version.version(parts_version._PARTS_VERSION[:-5])
    return version.version(parts_version._PARTS_VERSION)

def PartsExtensionVersion_env(env):
    return PartsExtensionVersion()

def generate_help_text():
    ''' The function defines the help text'''
    
    help='\n'+parts_version_text()+'''
Usage 'scons [scons options] [Parts options] [Targets]
Example: scons config=release foo

Use -H or --help-options for a list of scons options

Parts options:

BASIC SETTINGS:
    mode=modes,modeN       - Special build values to be passed to every Part.
                             (Default is 'default'.)
    tools=val[,valN]       - The preferred tool set to use when building.
    config=val[,valN]      - The configurations to build (Default is 'debug';
                             'release' is alternative).
    list_tool=all|tool_name- Dump defined configurations for the given tool or
                             dump information on every tool if 'all' is given.
    config_file=file_name  - Name of the config file to load with user settings.
                             (Default is 'parts.cfg' if it exits. All values in
                             the file are overridden by the command line.)
    duplicate_build=True|False
                           - Copy files to build_dir for safer parallel build
                             while developing. (Default is False - saves disks
                             space, is faster, and is less error prone.)
    use_env=True|False     - Use Shell enviroment instead of auto setup
                             (Default is False; FOR TEMPORARY USE ONLY!)
    verbose=x[,xn]         - Dump extra information about the current state;
                             values are 'all|...'. NOT YET IMPLEMENTED!
ADVANCED SETTINGS:
    BUILD_DIR_ROOT=dir     - Global root build directory to use.
                             (Default is './build'.)
    BUILD_DIR=build dir    - Global build directory to use.
                             (Default is '$BUILD_DIR_ROOT/${CONFIG}_${PLATFORM}
                             _${ARCHITECTURE}/$ALIAS'.)
    PREBUILT_SERVER=UNC    - Pre-built SDK repository location. (NO Default!)
    SVN_SERVER=URL         - SVN repository location. (NO Default!)
                             Use LocalSetup() piece to set these automatically.
    SVN_REVISION=XXXXX     - See "svn -r" (Default is None.)
    CHECK_OUT_ROOT=dir     - Root directory for file extraction;
                             (Default is './repository'.)
    CHECK_OUT_DIR=dir      - Part directory for file extraction;
                             (Default is '$CHECK_OUT_ROOT/$ALIAS'.)
    UPDATE_ALL=True|False  - Update files from all repositories at each build.
                             (Default is False)
    UPDATE_FROM_SVN=True|False
                           - Update files, but only from SVN (not prebuilts).
                             (Default is False)
    default_config=config  - Value of the default configuration; used when no
                             build configuration is given. (Default is 'debug'.)
    UTEST_ALL=value        - Value to use as the alias name used to build all
                             the known unit tests defined with env.Utest()
                             (Default is 'utest::')
    RUN_UTEST_ALL=value    - Value to use as the alias name used to run all the
                             known unit tests defined with env.Utest()
                             (Default is 'run_utest::')
    UNIT_TEST_ROOT=dir     - Global UnitTest directory to use.
                             (Default is './unit_tests'.)
    UNIT_TEST_DIR=dir      - Global build directory to use. (Default is
                             '$UNIT_TEST_ROOT/${CONFIG}_${PLATFORM}_
                             ${ARCHITECTURE}/${PART_PARENT_NAME}_${PART_VERSION}
                             /$UNIT_TEST_TARGET_NAME'.)
    USE_SRC_DIR=True|False - Value used for CPPPATH of dependent parts to
                             use the Src directory not the SDK directory.
                             Useful for debugging. (Default is 'False')
    '''
    
    SCons.Script.Help(help)

    

def process_part(alias):
    '''This function will figure out based on the processing of the database info
    if the part file should be used as is, modifed to use SDK part file (assumes 
    that the current SDK_ROOT path is correct) or if we should skip reading it.
    All of these steps are to help speed up the build by reducing what it added to 
    the Node set in SCons.
    '''

    def_env=SCons.Script.DefaultEnvironment()
    # test to see if we are reading any part file
    if common.g_buildable_part!=set():
        #if not see if we want to read this one
        if alias not in common.g_buildable_part:
            #if not here return None to skip processing this part
            return None
    
    #if we are here see if we should process this as a SDK or not
    if alias in common.g_build_as_sdk:
        #look like we should, so we need to get the sdk name
        sdkfile=common.g_depends_data[alias]['sdk_file']
        return sdkfile
    return [None]

def normalize_map(m):
    ''' doesn't do anything but look for certain key that might be in different 
    forms and translate them to a common one'''
    key='mode'
    value=m.get(key,None)
    if common.is_string(value) and not common.is_list(value):
        m[key]=string.split(value,',')
    
    key='tools'
    value=m.get(key,None)    
    if common.is_string(value) and not common.is_list(value):
        m[key]=common.process_tool_arg(string.split(value,','))

def process_conf_map(prepend,append,replace):
    '''make the config map we will use to create the Env
    it replaces then append and prepends data'''
    
    cfg_map={}
    cfg_map.update(common.g_args)
    cfg_map.update(replace)
    
    for i in append.keys():
        if cfg_map.has_key(i)==False:
            cfg_map[i]=append[i]
        else:
            cfg_map[i]+=append[i]
            
    for i in prepend.keys():
        if cfg_map.has_key(i)==False:
            cfg_map[i]=prepend[i]
        else:
            cfg_map[i]=append[i]+cfg_map[i]
    
    return cfg_map
        
    


### primary config stuff


def generate_config(prepend,append,replace):
    # get the tool list
    prepend_env=[]
    append_env=[]
    post_config=[] # these are settings that need to be tweaked after the 
    
    ## see if this was cached... seems to take long time to create an env
    ## so this is a big time saver.
    ## a big note should be given that this is not the best way to cache most
    ## likely but it is safe which is more important at the time of implementing this
    #global common.g_env_cache
    normalize_map(prepend)
    normalize_map(append)
    normalize_map(replace)
    cache_key=str(prepend)+str(append)+str(replace)
    cenv=common.g_env_cache.get(cache_key,None)
    
    if isinstance(cenv,SCons.Script.Environment):
        #print "using cached version"
        return cenv.Clone()
    else:
        #print "creating new env"
        pass
    
    #combine all maps with config settings
    cfg_map=process_conf_map(prepend,append,replace)  
    #This is the tools list we need look up
    tool_list=cfg_map['tools'] 
    # might need to map config in a different way later
    cfg_map['CONFIG']=cfg_map['config']
    
    # overwrite the tools key so SCon does not get upset
    # note the default is defined... needs to be defined first
    cfg_map['tools']=['default','packaging']    
    # add our mapper objects
    cfg_map['PARTS']=mappers.part_mapper
    cfg_map['PARTID']=mappers.part_id_mapper
    cfg_map['PARTSUB']=mappers.part_subst_mapper
    cfg_map['PARTNAME']=mappers.part_name_mapper
    cfg_map['PARTSHORTNAME']=mappers.part_shortname_mapper
    cfg_map['ABSPATH']=mappers.abspath_mapper
    cfg_map['RELPATH']=mappers.relpath_mapper
    
    
    for t in tool_list:
        #print t[0],t[1]
        cfg=config.get_config(cfg_map['CONFIG'],t[0],t[1])
        
        for ci in cfg.keys():
            if ci=='prepend_env':
                prepend_env.extend(cfg[ci])
            elif ci=='append_env':
                append_env.extend(cfg[ci])
            elif ci=='post_config':
                post_config.extend(cfg[ci])
            elif type(cfg[ci]) == type([]) and cfg_map.has_key(ci):
                cfg_map[ci]=common.make_unique(cfg_map[ci]+cfg[ci])
            elif type(cfg[ci]) == type({}) and cfg_map.has_key(ci):
                cfg_map[ci].update(cfg[ci]) # might not be the best choice?
            else:
                cfg_map[ci]=cfg[ci] # might not be the best choice?
                
    arch = cfg_map.get('ARCHITECTURE')
    if arch == None:
        arch = common.g_args['ARCHITECTURE']
    cfg_map['ARCHITECTURE'] = arch

    if arch != None:
        arch_tools = []
        for t in cfg_map['tools']:
            # Check if tool supports abi parameter and if it does
            # initialize the parameter.
            if type(t) == type(()) and type(t[1]) == type({}):
                if t[1].has_key('abi'):
                    t[1]['abi'] = arch
            arch_tools += [t]
        cfg_map['tools'] = arch_tools
    
    # post config stuff that needs to be based on everything else being done.
    # useful for setting up compatiblity flags on tools that might have been
    # set up before the dependent tool was.  For example, the Intel compiler
    # has flags to set up binary compatiblity with different VC and GCC versions.
    for i in post_config:
        i(cfg_map)
    env=SCons.Script.Environment(toolpath=[os.path.join(os.path.split(__file__)[0],'tools')],**cfg_map)
    
    # should not be needed most of the time, but it is useful
    # for old setups that need some extra care to build correctly.
    for i in prepend_env:
        env.PrependENVPath(i[0],i[1])
    for i in append_env:
        env.AppendENVPath(i[0],i[1])
    
    # this is a bit of a hack but it helps a lot .. here we append the system
    # path env value.. would be better if we did not do this but it helps with 
    # missing or other common tool issues at the current moment.. would like a
    # better solution when one has to use "other" non-python based solutions
    # like a way for us to extend the standard tools with our own.
    
    ## second note:  we want this to be at the end so we don't mess up the
    ## normal auto configuration stuff done by SCons for us!!!
    # we have to get the real scons path as for some reason appending does some 
    # unwanted behavior.. this fixes an issue with to compilers version paths
    # being on the PATH and the wrong one being first.. probably a feature
    # of scons for some linux users
    good_path=env['ENV']['PATH']
    env.AppendENVPath('PATH', os.environ['PATH'])
    # append the true path in front
    env.PrependENVPath('PATH', good_path)
    
    env.Append(BUILDERS = common.g_builders)
    
    if bool(env['use_env']) == True:
        env['ENV']=os.environ
    # current "cache"
    common.g_env_cache[cache_key]=env

    ## this is for fixing an issue with the scanners in which one item in a env
    ## does not have the $vars fully expanded, which causes an issue with in the
    ## dependency tree. This leads to a false rebuild of few files
    for k in SCons.Tool.SourceFileScanner.function.keys():
        if isinstance(SCons.Tool.SourceFileScanner.function[k].path_function,SCons.Scanner.FindPathDirs):
            SCons.Tool.SourceFileScanner.function[k].path_function=PartPathDirsWrapper(
            SCons.Tool.SourceFileScanner.function[k].path_function)
    
    #return the cached env
    return env.Clone()


class PartPathDirsWrapper:
    """This is a wrapper class to work around a "bug" with the scanner in that
    it tries to delay expand variables which might modify the Env. This
    allows use to expand the area in the env before it tries to create the tuple
    list of paths that it will use to scan with. The second improtance for this is 
    that an env may have been cloned, this catches cloned env cases as parts doesn't
    have a way to detect that the env was cloned"""
    def __init__(self, obj):
        self.obj = obj
        #print "$$$",obj.variable
    def __call__(self, env, dir, target=None, source=None, argument=None):
        def_env=SCons.Script.DefaultEnvironment()
        prop_lst=env.get(self.obj.variable,[])
        if prop_lst!=[]:
            ret=mappers.sub_lst(env,prop_lst,def_env)
            env[self.obj.variable]=ret
        #print 'Scanner', target[0]        
        return self.obj(env,dir,target,source,argument)


##def my_decider(dependency, target, prev_ni):
##    '''this function is used to decide if a node shoudl rebuild. The way we use it
##    is to add it to a value node, which has no value on disk to test for. We then
##    add this to a node, as a dependence, that is to be build so this value node
##    will call this function to decide if it needs to be built. Do this allow us to
##    set call a list of functors that will pre setup more dependencies to Scons, 
##    before Scons start to process them. This allow use to make a consistant
##    Enviroment to all node ( prevents false rebuilds) and allow use to set high 
##    level targets, map setting or what ever we need to do.'''
##    
##    print "MY DECIDER",dependency, target#, prev_ni.__dict__
##    def_env=SCons.Script.DefaultEnvironment()
##    if def_env['PREPROCESS_LOGIC_QUEUE']!=[]:
##        print "PARTS: Mapping version information"
##        for i in def_env['PREPROCESS_LOGIC_QUEUE']:
##            i()
##        def_env['PREPROCESS_LOGIC_QUEUE']=[]
##        print "PARTS: Done -- Mapping version information"
##    if common.g_args.get('REBUILD_ALL',False):
##        return True  
##    return False

def get_file_main_script(def_env):
    if def_env.GetOption('file')!=[]:
        return ''
    if os.path.exists('SConstruct'):
        return 'SConstruct'
    if os.path.exists('Sconstruct'):
        return 'SConstruct'
    if os.path.exists('sconstruct'):
        return 'SConstruct'
    return ''

def make_depends_map():
    #get def env
    def_env=SCons.Script.DefaultEnvironment()
    
    # for each alias get the 
    #  list of aliased that this depends on ( direct and indirect)
    #  part file name
    #  part file csig
    #  make_sdk 
    #  sdk_file name
    #  the alias -> target mappings
    #  the root part name.. need to tell the base file we need to read in case of subparts
    data={}
    for a in def_env['PART_INFO'].itervalues():
        alias=a['ALIAS']
        if (a['ROOT_ALIAS'] not in common.g_build_as_sdk) and ((alias in common.g_buildable_part) or common.g_buildable_part==set()):
            env=a['ENV']
            tmp={}
            # the depends
            tmp['depends']=set(functors.full_parts_depends_list(a['ENV']))
            f=a['FILE']

            # the file
            tmp['file_name']= f.srcnode().path
            
            # the file csig
            tmp['csig']=f.get_csig()
            #  sdk_file
            tf = env.subst('$PART_NAME')+'_'+env.subst('$PART_VERSION')
            tout=os.path.join('$SDK_ROOT',tf+'.sdk.parts')
            tmp['make_sdk']=a['MAKES_SDK']
            f=a.get('SDK_FILE',None)
            if f != None:
                tmp['sdk_file']=f.path
            
            # the alias to target map
            targets=set()
            for i in common.g_name_alias_map[alias]:
                targets.add(env.subst(i))
            tmp['targets']= targets
            # the root part
            tmp['root_part']=a['ROOT_ALIAS']
                    
            data[alias]=tmp
    s=get_file_main_script(def_env)
    if s=='':
        data["SConstruct_file"]=0
    else:
        fn=def_env.File(s)
        if fn.exists():
            data["SConstruct_file"]=fn.get_csig()
        else:
            data["SConstruct_file"]=0
    return data

def store_depends_data():
    import cPickle
    tmp=make_depends_map()
    # if we are not using SDK and we are reading everything, just re-write the whole file 
    if (common.g_args['use_sdk']==False and common.g_buildable_part == set()):
        common.g_depends_data=tmp
    else:
        #else we only update what we know is safe.
        common.g_depends_data.update(tmp)
    output = open('.parts.depends', 'wb')
    cPickle.dump(common.g_depends_data, output)
    common.g_depends_data=None
    output.close()
    
def load_depends_data():
    try:
        import cPickle
        if os.path.exists('.parts.depends'):
            output = open('.parts.depends', 'rb')
            stored_data=cPickle.load(output)
            tmp=stored_data["SConstruct_file"]
            del stored_data["SConstruct_file"]
            output.close()
            return (tmp,stored_data)
    except Exception,ec:
        pass
    return (0,{})

def parts_prebuild_setup():
    def_env=SCons.Script.DefaultEnvironment()
    if def_env['PREPROCESS_LOGIC_QUEUE']!=[]:
        rpt=def_env['PARTS_REPORTER']
        rpt.part_message("Mapping version information")
        
        store_depends_data()
        
        for i in def_env['PREPROCESS_LOGIC_QUEUE']:
            i()
        def_env['PREPROCESS_LOGIC_QUEUE']=[]
        rpt.part_message("Done -- Mapping version information")
    return True


import SCons.Script.Main
scons_build_targets = SCons.Script.Main._build_targets

def _build_targets(fs, options, targets, target_top):
    #print "&&&",common.g_name_alias_map
    
    if parts_prebuild_setup() == False:
        return None
    return scons_build_targets(fs, options, targets, target_top)

SCons.Script.Main._build_targets = _build_targets



# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.PartVersionString=parts_version_text_env
SConsEnvironment.IsPartsExtensionVersionBeta=is_parts_version_beta_env
SConsEnvironment.PartsExtensionVersion=PartsExtensionVersion_env

common.add_config_var('REBUILD_ALL',False)

common.add_parts_object('PartVersionString',parts_version_text)
common.add_parts_object('IsPartsExtensionVersionBeta',is_parts_version_beta)
common.add_parts_object('PartsExtensionVersion',PartsExtensionVersion)
