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
import tool_mapping
import Variables

import platform_info

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

def generate_help_text2():
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
    
    key='tool_chain'
    value=m.get(key,None)    
    if common.is_string(value) and not common.is_list(value):
        m[key]=common.process_tool_arg(string.split(value,','))
    
    return m


### primary config stuff


def generate_config(prepend,append,replace):
    
    ## see if this was cached... seems to take long time to create an env
    ## so this is a big time saver as most of the time we only need a copy of the 
    ## same setup
    ## NOTE!! should be given that this is not the best way to cache most likely
    ## but it is safe which is more important at the time of implementing this

    cache_key=str(normalize_map(prepend))+\
                str(normalize_map(append))+\
                str(normalize_map(replace))+\
                str(normalize_map(common.g_defaultoverides))
                
    env=common.g_env_cache.get(cache_key,None)
    
    #if not isinstance(env,SCons.Script.Environment):
    if env is None:
        
        ## basic setup
        cfg_map={}
        overrides=SCons.Script.ARGUMENTS.copy()
        overrides.update(replace)
        # minor messing around with tools still need 
        pre_tools=prepend.get('tool_chain',[])
        if pre_tools:
            del prepend['tool_chain']
        post_tools=append.get('tool_chain',[])
        if post_tools:
            del append['tool_chain']
        # add stuff in SCons that are tools, that are needed
        # this is needed for Tag for Install()
        post_tools.append('packaging')

        ## setup the SCons Variable
        cfg_files=[SCons.Script.GetOption('cfg_file')]
        vars=Variables.Variables(cfg_files,args=overrides,user_defaults=common.g_defaultoverides)
        vars.AddVariables(*common.def_vars)
        
        ## set readonly values
        # add our mapper objects
        cfg_map.update(common.g_mappers)
        # random data
        cfg_map["PARTS_MODE"]=common.g_part_mode
        if SCons.Script.GetOption('keep_going'):
            cfg_map["CONTINUE_ON_EXCEPTION"]=True
        else:
            cfg_map["CONTINUE_ON_EXCEPTION"]=False
        
        ## create a new environment
        # get our toolpath 
        tool_path=[os.path.join(os.path.split(__file__)[0],'tools')]
        # make the SCons environment
        env=SCons.Script.Environment(
                                variables = vars,
                                tools=[],
                                toolpath=tool_path,
                                BUILDERS = common.g_builders,
                                **cfg_map
                                )
        # since we don't have overides in the __init__call??
        env['HOST_PLATFORM']=platform_info._host_sys
        
        # core variable remapings
        #env['CONFIG']=env.subst('${config}')
        #print env.Dump("TARGET_PLATFORM")
        #print cfg_map
        ## apply tool chain
        #print env['tool_chain']
        env.ToolChain(pre_tools+env['tool_chain']+post_tools)#tl_chain)
        ## apply the configuration for the tool    
        #config.Configuration(env)
        config.apply_config(env)            
        
        #append any data or prepend any data as needed
        #will probally need better error handling later
        for k,v in append.iteritems():
            has_hey=env.has_key(k)
            if common.is_list(v) and has_hey:
                env.AppendUnique(**{k:v})
            elif common.is_list(v) and not has_hey:
                env[k]=v
            else:
                print "error",k,"is not a list"
        
        for k,v in prepend.iteritems():
            has_hey=env.has_key(k)
            if common.is_list(v) and has_hey:
                env.PrependUnique(**{k:v})
            elif common.is_list(v) and not has_hey:
                env[k]=v
            else:
                print "error",k,"is not a list"
                
        
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
    ##    good_path=env['ENV']['PATH']
    ##    env.AppendENVPath('PATH', os.environ['PATH'])
    ##    # append the true path in front
    ##    env.PrependENVPath('PATH', good_path)
    ##    

        if bool(env['use_env']) == True:
            env['ENV']=os.environ

        ## this is for fixing an issue with the scanners in which one item in a env
        ## does not have the $vars fully expanded, which causes an issue with in the
        ## dependency tree. This leads to a false rebuild of few files
        for k in SCons.Tool.SourceFileScanner.function.keys():
            if isinstance(SCons.Tool.SourceFileScanner.function[k].path_function,SCons.Scanner.FindPathDirs):
                SCons.Tool.SourceFileScanner.function[k].path_function=PartPathDirsWrapper(
                SCons.Tool.SourceFileScanner.function[k].path_function)
        
        # Add this to cache
        common.g_env_cache[cache_key]=env    
    
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
    if (common.g_part_mode==False and common.g_buildable_part == set()):
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

common.AddBoolVariable('REBUILD_ALL',False,'')

common.add_parts_object('PartVersionString',parts_version_text)
common.add_parts_object('IsPartsExtensionVersionBeta',is_parts_version_beta)
common.add_parts_object('PartsExtensionVersion',PartsExtensionVersion)
