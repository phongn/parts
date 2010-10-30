## the core logic

import fnmatch
import shutil
import os
import sys
import string
import stat

import SCons.Script 

import load_module
import pattern
import config
import common 
import version
import mappers
import functors
import tool_mapping
import Variables
import logger
import reporter

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
        tmp=common.process_tool_arg(string.split(value,','))
        tmp.reverse()
        m[key]=tmp
    
    return m


### primary config stuff

# class to handle old stuff that needs to change.. move to better location later
class deprecated:
    def __init__(self,key,new_key,value):
        self.key=key
        self.new_key=new_key
        self.value=value

    def __str__(self):
        #reporter.SetPartStackFrameInfo()
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        #reporter.ResetPartStackFrameInfo()
        return self.value

    def __eq__(self,rhs):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return self.value == rhs

    def __ne__(self,rhs):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return self.value != rhs    
    
    def __hash__(self):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return hash(str(self.value))
    
    def __len__(self):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return len(str(self.value))
    def __getitem__(self,key):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return self.value[key]
    
    def __add__(self, other):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return self.value+other
    def __radd__(self, other):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return other+self.value
    def __contains__ (self,item):
        reporter.report_warning("[",self.key,"] is deprecated please use [",self.new_key,"]")
        return item in self.value
        

class string_tester(object):
    def __init__(self,value):
        self.value=value
    
    def __eq__(self,rhs):
        import fnmatch
        return fnmatch.fnmatchcase(rhs, self.value)

def get_cache_values(*lst):
    cache_values=[
        string_tester('*')
##        string_tester('TARGET_*'),
##        string_tester('*_VERSION'),
##        string_tester('*_SCRIPT'),
##        string_tester('*_INSTALL_ROOT'),
##        'use_env',
##        'config',
##        'CONFIG',
##        'toolchain',
##        'tools', # to be removed
##        'ARCHITECTURE', #to be removed
##        'PLATFORM' # for safety in SCons
        ]
    ret=''
    for l in lst:
        for i in l:
            if i in cache_values:
                ret+="%s=%s"%(i,l[i])
        
    return ret
            


def generate_config(prepend,append,replace):
    
    ## see if this was cached... seems to take long time to create an env
    ## so this is a big time saver as most of the time we only need a copy of the 
    ## same setup
    ## NOTE!! should be given that this is not the best way to cache most likely
    ## but it is safe which is more important at the time of implementing this

    cache_key=get_cache_values(normalize_map(prepend),
                                normalize_map(append),
                                normalize_map(replace),
                                normalize_map(common.g_defaultoverides))


                
    env=common.g_env_cache.get(cache_key,None)
        
    #if not isinstance(env,SCons.Script.Environment):
    if env is None:
        
        ## basic setup
        cfg_map={}
        import copy
        # get command line args
        
        #print SCons.Script.ARGUMENTS
        overrides=copy.deepcopy(SCons.Script.ARGUMENTS)
        
        ##################################
        ## test for bad value.. remap is needed
        tmp=overrides.get('tools',[])
        if tmp!=[]:
            reporter.report_warning('tools is deprecated, use toolchain',env=env)
            if overrides.has_key('toolchain')==False:
                overrides['toolchain']=tmp
            del overrides['tools']

        # test for bad value.. remap is needed
        tmp=replace.get('tools',[])
        if tmp!=[]:
            reporter.report_warning('tools is deprecated, use toolchain',env=env)
            if replace.has_key('toolchain')==False:
                replace['toolchain']=tmp
            del replace['tools']

        tmp=prepend.get('tools',[])
        if tmp!=[]:
            reporter.report_warning('tools is deprecated, use toolchain',env=env)
            if prepend.has_key('toolchain')==False:
                prepend['toolchain']=tmp
            del prepend['tools']

        tmp=append.get('tools',[])
        if tmp!=[]:
            reporter.report_warning('tools is deprecated, use toolchain',env=env)
            if append.has_key('toolchain')==False:
                append['toolchain']=tmp
            del append['tools']

        ## ARCH stuff

        tmp=overrides.get('ARCHITECTURE',None)
        if tmp is not None:
            reporter.report_warning('ARCHITECTURE is deprecated, use TARGET_PLATFORM',env=env)
            if overrides.has_key('TARGET_ARCH')==False and overrides.has_key('TARGET_PLATFORM')==False:
                tmp={'TARGET_PLATFORM':platform_info.SystemPlatform(os='any',arch=tmp)}
                overrides.update(tmp)

        # test for bad value.. remap is needed
        tmp=replace.get('ARCHITECTURE',None)
        if tmp is not None:
            reporter.report_warning('ARCHITECTURE is deprecated, use TARGET_PLATFORM',env=env)
            if replace.has_key('TARGET_ARCH')==False and replace.has_key('TARGET_PLATFORM')==False:
                tmp={'TARGET_PLATFORM':platform_info.SystemPlatform(os='any',arch=tmp)}
                overrides.update(tmp)

        tmp=append.get('ARCHITECTURE',None)
        if tmp is not None:
            reporter.report_warning('ARCHITECTURE is deprecated, use TARGET_PLATFORM',env=env)
            if append.has_key('TARGET_ARCH')==False and append.has_key('TARGET_PLATFORM')==False:
                tmp={'TARGET_PLATFORM':platform_info.SystemPlatform(os='any',arch=tmp)}
                overrides.update(tmp)

        tmp=prepend.get('ARCHITECTURE',None)
        if tmp is not None:
            reporter.report_warning('ARCHITECTURE is deprecated, use TARGET_PLATFORM',env=env)
            if prepend.has_key('TARGET_ARCH')==False and prepend.has_key('TARGET_PLATFORM')==False:
                tmp={'TARGET_PLATFORM':platform_info.SystemPlatform(os='any',arch=tmp)}
                overrides.update(tmp)
            
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
        post_tools.extend(['install','zip'])
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
        cfg_map["PARTS_MODE"]=common.g_engine._build_mode
        if SCons.Script.GetOption('keep_going'):
            cfg_map["CONTINUE_ON_EXCEPTION"]=True
        else:
            cfg_map["CONTINUE_ON_EXCEPTION"]=False
        
        ## create a new environment
        ## get our toolpath 
        tool_path=load_module.get_site_directories('tools')
        # make the SCons environment #############################
        env=SCons.Script.Environment(
                                #variables = vars,
                                tools=[],
                                toolpath=tool_path,
                                BUILDERS = common.g_builders,
                                **cfg_map
                                )
        
        vars.Update(env)
        # since we don't have overides in the __init__call??
        env['HOST_PLATFORM']=platform_info._host_sys
        env['_BUILD_CONTEXT_FILES']=set()
        # update the missing arguments to enviroment stuff
        # this is stuff that does not have a option defined for
        #update_extra_options(env)
        env.PrependENVPath('PATH',os.path.split(sys.executable)[0],delete_existing=True)
        env.Replace(**vars.UnknownVariables())
        ## apply tool chain
        env.ToolChain(pre_tools+env['toolchain']+post_tools)#tl_chain)
        
        ## apply the configuration for the tool    
        env.Configuration()
        #config.apply_config(env)            
        
        #append any data or prepend any data as needed
        #will probally need better error handling later
        for k,v in append.iteritems():
            has_hey=env.has_key(k)
            if common.is_list(v) and has_hey:
                env.AppendUnique(**{k:v})
            elif common.is_list(v) and not has_hey:
                env[k]=v
            else:
                reporter.report_warning('Ignoring appending value', k,"as it is not a list. It is type",type(v),".")
        
        for k,v in prepend.iteritems():
            has_hey=env.has_key(k)
            if common.is_list(v) and has_hey:
                env.PrependUnique(**{k:v})
            elif common.is_list(v) and not has_hey:
                env[k]=v
            else:
                reporter.report_warning('Ignoring prepending value', k,"as it is not a list. It is type",type(v),".")


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
        import overrides
        overrides.scanner.Scanner_override()

        # stuff to zap
        env["ARCHITECTURE"]=deprecated("ARCHITECTURE","TARGET_ARCH",env['TARGET_ARCH'])
        env["config"]=deprecated("config","CONFIG",env['CONFIG'])
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

    

import time
def part_object_setup():
    reporter.print_msg("Processing Part objects")
    total_file_install=0
    total_file_build=0
    total_parts=0
    total_subparts=0
    total_src=0
    total_nodes=0
    for i in common.g_parts.keys():
        reporter.print_msg("Processing Part:", i)
        tmp=common.g_parts[i]
        start=time.time()
        #tmp.Process()
        total_file_build += len(tmp.target_files)
        total_file_install += len(tmp.installed_files)
        total_parts+=1
        total_src+= len(tmp.source_files)
        total_nodes= total_src+total_file_build
        print "*****", tmp.alias,time.time()-start
        print 'tally total_parts',total_parts
        print 'tally total_subparts',total_subparts
        print 'tally total_file_build',total_file_build
        print 'tally total_file_install',total_file_install
        print 'tally total_src',total_src
        print 'tally total_nodes',total_nodes
        for sub in tmp.sub_parts.values():
            total_file_build += len(sub.target_files)
            total_file_install += len(sub.installed_files)
            total_parts+=1
            total_subparts+=1
            print '---',sub.alias
            print 'tally total_parts',total_parts
            print 'tally total_subparts',total_subparts
            print 'tally total_file_build',total_file_build
            print 'tally total_file_install',total_file_install
            print 'tally total_src',total_src
            print 'tally total_nodes',total_nodes
        
        #print "end",i
    print 'total_parts',total_parts
    print 'total_subparts',total_subparts
    print 'total_file_build',total_file_build
    print 'total_file_install',total_file_install
    print 'total_src',total_src
    print 'total_nodes',total_nodes
    reporter.print_msg("Finished processing Part objects")

##import SCons.Script.Main
##scons_build_targets = SCons.Script.Main._build_targets
##
##
##def _build_targets(fs, options, targets, target_top):
##    #print "&&&",common.g_name_alias_map
##    reporter.SetPartStackFrameInfo()
##    part_object_setup()
##    if parts_prebuild_setup() == False:
##        ret= None
##    else:
##        ret= scons_build_targets(fs, options, targets, target_top)
##
##    reporter.ResetPartStackFrameInfo()
##    return ret
##
##SCons.Script.Main._build_targets = _build_targets

class ToolChain():
    
    def Exists(name,**kw):
        pass

class All:
    def __init__(self,*lst):
        self.lst=lst
        
    def Valid(self,tester):
        for i in self.lst:
            if tester(i)==False:
                return False
        return True
    
    def GetValues(self):
        return self.lst
        


class OneOf:
    def __init__(self,*lst):
        self.lst=lst
        
    def Valid(self,tester):
        for i in self.lst:
            if tester(i)==True:
                return True
        return False
    
    def GetValues(self,tester):
        for i in self.lst:
            if tester(i)==True:
                return [i]
        return []
        
class AnyOf:
    def __init__(self,*lst):
        self.lst=lst        
        
    def Valid(self,tester):
        for i in self.lst:
            if tester(i)==True:
                return True
        return False
    
    def GetValues(self,tester):
        ret=[]
        for i in self.lst:
            if tester(i)==True:
                ret.append(i)
        return ret



# move to a new file to remove core.py

class parts_dict(dict):
    def __getattr__(self,name):
        return self[name]
    
    def __setattr__(self,name,value):
        if is_dictionary(value):
            self[name]=parts_dict(value)
        else:
            self[name]=value
            
    def __delattr__(self,name):
        del self[name]
    

class XXX:
    
    __env_chache={} 
    
    def __init__(self):
        dict.__init__(self,kw)
        self['vars']=namespace()
        self['options']=namespace()
        
        
    
    ## stuff for self.value logic
    def __getattr__(self,name):
        return self[name]
    def __setattr__(self,name,value):
        self[name]=value
    def __delattr__(self,name):
        del self[name]

    def SetOptionDefault(self,):
        pass
        
    # option get --<name>
    def AddOption(self,): pass
    def BoolOption(self,): pass
    def FeatureOption(self,): pass# like a bool --enable-<name> --disable-name
    def EnumOption(self,):pass
    def ListOption(self,):pass
    def IntOption(self,):pass
    def PathOption(self,):pass
        
    def GetOption(self,name):
        return 
    
    # Variables are <name>=Value
    def AddVariable(self,):pass
    def BoolVariable(self,):pass
    def FeatureVariable(self,):pass
    def EnumVariable(self):pass
    def ListVariable(self):pass
    def PathVariable(self):pass
        
    def getVariable(self,name):
        ''' return the value of a varaible based on a cached Env of the current state'''
        return 
    
    def ToolChain(self,name):
        return ToolChain(name)
        
    def Configuration(self,name,default_ver_func,post_process_func=None):
        return self.Config_Set.Configuration(default_ver_func,post_process_func)

    def Environment(self,**kw):
        '''
        This makes a environment with the toolchain and configruation set on it
        '''
        pass
        
    def BasicEnvironment(self):
        ''' 
        This makes a minimum environment with no tool or configuration setup
        ''' 
        pass
    
    def Component(self,):
        return self.Part()
        
    def Part(self):
        return Part_t(config_content=self,)
        
    def __has_env_chached():
        ''' tells is the current state of this configuration object has a chached 
        environment created yet.
        '''

def DefaultXXX():
    pass

def DefaultEnvironment():
    pass

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

common.AddBoolVariable('REBUILD_ALL',False,'')
