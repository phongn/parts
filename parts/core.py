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
import env_overrides

import platform_info
    
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
    
    key='toolchain'
    value=m.get(key,None)    
    if common.is_string(value) and not common.is_list(value):
        m[key]=common.process_tool_arg(string.split(value,','))
    
    return m


### primary config stuff

class deprecated:
    def __init__(self,key,new_key,value):
        self.key=key
        self.new_key=new_key
        self.value=value

    def __str__(self):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return self.value

    def __eq__(self,rhs):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return self.value == rhs

    def __ne__(self,rhs):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return self.value != rhs    
    
    def __hash__(self):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return hash(str(self.value))
    
    def __len__(self):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return len(str(self.value))
    def __getitem__(self,key):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return self.value[key]
    
    def __add__(self, other):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return self.value+other
    def __radd__(self, other):
        rpt=SCons.Script.DefaultEnvironment().get('PARTS_REPORTER',None)
        rpt.part_warning(None,"["+self.key+"] is deprecated please use ["+self.new_key+"]")
        return other+self.value

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
    # temp disabling of the cache as the Clone() has a leak in it

    #if not isinstance(env,SCons.Script.Environment):
    if env is None:
        def_env=SCons.Script.DefaultEnvironment()
        rpt=def_env.get('PARTS_REPORTER',None)
        ## basic setup
        cfg_map={}
        # get command line args
        overrides=SCons.Script.ARGUMENTS.copy()
        ##################################
        ## test for bad value.. remap is needed
        tmp=overrides.get('tools',[])
        if tmp!=[]:
            rpt.part_warning(env,'tools is deprecated, use toolchain')
            if overrides.has_key('toolchain')==False:
                overrides['toolchain']=tmp
            del overrides['tools']

        # test for bad value.. remap is needed
        tmp=replace.get('tools',[])
        if tmp!=[]:
            rpt.part_warning(env,'tools is deprecated, use toolchain')
            if replace.has_key('toolchain')==False:
                replace['toolchain']=tmp
            del replace['tools']

        tmp=prepend.get('tools',[])
        if tmp!=[]:
            rpt.part_warning(env,'tools is deprecated, use toolchain')
            if prepend.has_key('toolchain')==False:
                prepend['toolchain']=tmp
            del prepend['tools']

        tmp=append.get('tools',[])
        if tmp!=[]:
            rpt.part_warning(env,'tools is deprecated, use toolchain')
            if append.has_key('toolchain')==False:
                append['toolchain']=tmp
            del append['tools']

        ## ARCH stuff

        tmp=overrides.get('ARCHITECTURE',None)
        if tmp is not None:
            rpt.part_warning(env,'ARCHITECTURE is deprecated, use TARGET_PLATFORM')
            if overrides.has_key('TARGET_ARCH')==False or overrides.has_key('TARGET_PLATFORM')==False:
                overrides['TARGET_PLATFORM']=platform_info.SystemPlatform(os='any',arch=tmp)

        # test for bad value.. remap is needed
        tmp=replace.get('ARCHITECTURE',None)
        if tmp is not None:
            rpt.part_warning(env,'ARCHITECTURE is deprecated, use TARGET_PLATFORM')
            if replace.has_key('TARGET_ARCH')==False or replace.has_key('TARGET_PLATFORM')==False:
                overrides['TARGET_PLATFORM']=platform_info.SystemPlatform(os='any',arch=tmp)

        tmp=append.get('ARCHITECTURE',None)
        if tmp is not None:
            rpt.part_warning(env,'ARCHITECTURE is deprecated, use TARGET_PLATFORM')
            if append.has_key('TARGET_ARCH')==False or append.has_key('TARGET_PLATFORM')==False:
                overrides['TARGET_PLATFORM']=platform_info.SystemPlatform(os='any',arch=tmp)

        tmp=prepend.get('ARCHITECTURE',None)
        if tmp is not None:
            rpt.part_warning(env,'ARCHITECTURE is deprecated, use TARGET_PLATFORM')
            if prepend.has_key('TARGET_ARCH')==False or prepend.has_key('TARGET_PLATFORM')==False:
                overrides['TARGET_PLATFORM']=platform_info.SystemPlatform(os='any',arch=tmp)        
            
        ######################################            
        overrides.update(replace)
        
        # minor messing around with tools still need 
        # (replace should get the toolchain of this)
        pre_tools=prepend.get('toolchain',[])
        if pre_tools!=[]:
            del prepend['toolchain']
        post_tools=append.get('toolchain',[])
        if post_tools!=[]:
            del append['toolchain']
        # add stuff in SCons that are tools, that are needed
        # this is needed for Tag for Install()
        post_tools.extend(['packaging','install','zip'])
        ## setup the SCons Variable
        cfg_files=[SCons.Script.GetOption('cfg_file')]
        vars=Variables.Variables(cfg_files,args=overrides,user_defaults=common.g_defaultoverides)
        vars.AddVariables(*common.def_vars)

        # adds values that may not be set as an Varibiable        
        cfg_map.update(common.g_defaultoverides)
        # add our mapper objects
        cfg_map.update(common.g_mappers)
        # random data
        #cfg_map['HOST_PLATFORM']=platform_info._host_sys
        cfg_map["PARTS_MODE"]=common.g_part_mode
        if SCons.Script.GetOption('keep_going'):
            cfg_map["CONTINUE_ON_EXCEPTION"]=True
        else:
            cfg_map["CONTINUE_ON_EXCEPTION"]=False
        
        ## create a new environment
        # get our toolpath 
        tool_path=[os.path.join(os.path.split(__file__)[0],'tools')]
        # make the SCons environment #############################
        env=SCons.Script.Environment(
                                variables = vars,
                                tools=[],
                                toolpath=tool_path,
                                BUILDERS = common.g_builders,
                                **cfg_map
                                )
        #print "Unknowns *********************"
        #print vars.UnknownVariables()
        #print "******************************"
    
        # since we don't have overides in the __init__call??
        env['HOST_PLATFORM']=platform_info._host_sys
        # update the missing arguments to enviroment stuff
        # this is stuff that does not have a option defined for
        #update_extra_options(env)
        env.Replace(**vars.UnknownVariables())
        
        # stuff to zap
        env["ARCHITECTURE"]=deprecated("ARCHITECTURE","TARGET_ARCH",env['TARGET_ARCH'])
    
        ## apply tool chain
        env.ToolChain(pre_tools+env['toolchain']+post_tools)#tl_chain)
        
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

        if env['HOST_PLATFORM']['OS'] =='win32':
            # add certain paths for windows
            env.AppendENVPath('PATH',SCons.Platform.win32.get_system_root(), delete_existing=1)
            env.AppendENVPath('PATH',SCons.Platform.win32.get_system_root()+'\\system32', delete_existing=1)            
            
        
        # this allow the user to set the enviroment to the user path
        # hopefully this is not needed 99.9% of the time.
        # if used it will use the user env, and ignore the setup the SCons did
        # minus the setup of the builder and flags
        if bool(env['use_env']) == True:
            env['ENV']=os.environ

        ## this is for fixing an issue with the scanners in which one item in a env
        ## does not have the $vars fully expanded, which causes an issue with in the
        ## dependency tree. This leads to a false rebuild of few files
        env_overrides.Scanner_override()
        
        # Add this to cache
        common.g_env_cache[cache_key]=env    
    
    #return the cached env
    return env.Clone()





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

common.AddBoolVariable('REBUILD_ALL',False,'')
