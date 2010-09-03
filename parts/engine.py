
import common
import reporter
import logger
import poptions# want to remove
import core# want to remove
import load_module
import part_manager
import datacache
import target_type

import SCons.Script    

import SCons.Node.FS

import sys
import os
import stat
import atexit
import pprint
import hashlib
import copy
from cStringIO import StringIO
    
################################################################################

import time

def get_Sconstruct_files():
    '''
    get the names of all the "top level" SConstruct files being processed
    Need to see if there is a better SCons function for this
    '''
    #Get the name of the SConstruct file... as the user mighthave used -F
    fnames=SCons.Script.GetOption('file')
    if fnames == []:
        # check current directory to see if what "default" file exits
        if os.path.exists("SConstruct"):
            fnames=["SConstruct"]
        elif os.path.exists("Sconstruct"):
            fnames=["Sconstruct"]
        elif os.path.exists("sconstruct"):
            fnames=["sconstruct"]
    
    return fnames
    
def is_Sconstruct_up_to_date():
    '''
    This functions will tell us if the Sconstruct file looks as if it has changed
    by checking the MD5
    '''
    
    fnames=get_Sconstruct_files()
    data=datacache.GetCache("global_data")
    ret=True
    if data is None:
        reporter.verbose_msg("update_check",'No datacache For SConstruct file found')
        return False
    for i in fnames:
        try:
            tmp=data['sconstruct_files'][i]
        except KeyError:
            # should not happen... but the file have been updated during development
            return False
        # see if the part file is different
        if os.path.isfile(i):
            # it should exist
            if os.stat(i)[stat.ST_MTIME] != tmp['timestamp']:
                # time stamp is different .. check csig to be sure
                if common.g_engine.def_env.File(i).get_csig() != tmp['csig']:
                    reporter.verbose_msg("update_check","File: %s has changed"%(i))
                    ret=False
        else:
            reporter.verbose_msg("update_check",'File: %s does not exist'%(i))
            ret=False
    
    return ret

    

###################
import types

def get_content(obj):
    
    ret=None
##    try:
##        print obj.__class__
##    except:
##        try:
##            print obj.__name__
##        except:
##            print type(obj)
    # Is this a function?
    if isinstance(obj,types.LambdaType) or \
        isinstance(obj,types.MethodType  ) or \
        isinstance(obj,types.FunctionType ) or\
        isinstance(obj,types.InstanceType ) or \
        isinstance(obj,types.ClassType  ) or \
        isinstance(obj,types.FunctionType ) or\
        isinstance(obj,types.CodeType):
        return SCons.Action._object_contents(obj)
    
    elif isinstance(obj,types.DictionaryType):
        ret='{'
        for k,v in obj.items():
            ret+="%s:%s,"%(k,get_content(v))
        ret+=']'
    elif isinstance(obj,types.TupleType) or\
        isinstance(obj,types.GeneratorType ) or\
        isinstance(obj,types.ListType):
        ret='['
        for i in obj:
            ret+="%s,"%get_content(i)
        ret+=']'
    else:
        ret=str(obj)
            
    return ret



def get_defining_file_from_object(obj):
    
    ret=None
##    try:
##        print obj.__class__
##    except:
##        try:
##            print obj.__name__
##        except:
##            print type(obj)
    # Is this a function?
    if isinstance(obj,types.LambdaType) or \
        isinstance(obj,types.MethodType  ) or \
        isinstance(obj,types.FunctionType ):
        ret=obj.func_code.co_filename
      
    elif isinstance(obj,types.InstanceType ) or \
        isinstance(obj,types.ClassType  ) or \
        isinstance(obj,types.FunctionType ):
        tmp = dir(obj)    
        for i in tmp:
            get_defining_file_from_object(getattr(obj,i))
            
    # is it a code type
    elif isinstance(obj,types.CodeType):
        ret=obj.co_filename
        print "code object",ret
    elif isinstance(obj,types.DictionaryType) or\
        isinstance(obj,types.TupleType) or\
        isinstance(obj,types.GeneratorType ) or\
        isinstance(obj,types.ListType):
        #print "in iterable object"
        for i in obj:
            get_defining_file_from_object(i)
    #else:
        #print type(obj)#,dir(obj)
            
    return ret
            

g_mod_dict={}
def get_import_list(mod):
    
    try:
        return g_mod_dict[mod.__name__]
    except KeyError:
        ret=set()
        for m in mod.__dict__.values():
            if isinstance(m,types.ModuleType):
                if m.__name__ not in g_mod_dict:
                    try:
                        tmp=m.__file__
                        
                        if tmp.endswith('.pyc'):
                            #replace with py file.. as we want to check this guy
                            tmp=tmp[:-3]+"py"
                        ret.add(tmp)
                        g_mod_dict[mod.__name__]=set()
                        ret.update(get_import_list(m))
                    except AttributeError:
                        g_mod_dict[m.__name__]=set()
                else:
                    ret.update(get_import_list(m))
        g_mod_dict[mod.__name__]=ret
        return ret

# we try to write this as if this was a method on the node objects
#so self is the node...

def get_context_files(self):
    
    action_obj=self.builder.action
    ret=[]
    if isinstance(action_obj,SCons.Action.FunctionAction):        
        ret.append(get_defining_file_from_object(action_obj.execfunction))
        
        
    elif isinstance(action_obj,SCons.Action.ListAction):
        for l in action_obj.list:            
            if isinstance(l,SCons.Action.FunctionAction):
                ret.append(get_defining_file_from_object(l.execfunction))
                
        
##    elif isinstance(action_obj,SCons.Action.LazyAction):
##        #pp.pprint(action_obj.__dict__)
##        pass
##         
##    elif isinstance(action_obj,SCons.Action.CommandGeneratorAction):
##        #print action_obj.__class__,":",action_obj.get_contents(self,self.sources,self.env)
##        pass
##    #elif isinstance(action_obj,SCons.Action.CommandAction):
##    #    print action_obj.__class__,":",action_obj.get_contents(self,self.sources,self.env)
##    #    pass
##    else:
##        #print action_obj.__class__, '*************',self
##        #pp.pprint(action_obj.__dict__)
##        #print action_obj.get_contents(self,self.sources,self.env)
##        pass
    return ret
        

def add_builder_context_files(pobj,builder):
    # see if this Part knows of this builder
    
    try:
        ret=add_builder_context_files.cache[pobj.Root.Alias+builder.get_name(pobj.Env)]
        pobj._add_build_context_files(ret)
        return
    except AttributeError:
        add_builder_context_files.cache={}
    except KeyError:
        pass
    action_obj=builder.action
    ret=[]
    if isinstance(action_obj,SCons.Action.FunctionAction):        
        ret.append(get_defining_file_from_object(action_obj.execfunction))
        
        
    elif isinstance(action_obj,SCons.Action.ListAction):
        for l in action_obj.list:            
            if isinstance(l,SCons.Action.FunctionAction):
                tmp=get_defining_file_from_object(l.execfunction)
                if tmp:
                    ret.append(tmp)
        
    add_builder_context_files.cache[pobj.Root.Alias+builder.get_name(pobj.Env)]=ret
    pobj._add_build_context_files(ret)
     
        



################





# would it be nice if ther was a addon base in Scons... hmmmmm
class parts_addon(object):
    def __init__(self):
        
        # some known data items
        self.__part_manager=None
        self.def_env=None
        self.__post_process_queue=[]
        self.__cache_key=None
        self.__build_mode=None
        
        # start up the reporter which controls the streams and all output
        use_color=SCons.Script.GetOption('use_color')
        # need to trace this before we set the colors else the tests break
        reporter.trace_msg("use_color_option","use_color =",use_color)
        redirected=os.isatty(sys.__stdout__.fileno()) ==False or os.isatty(sys.__stderr__.fileno()) ==False        
        if use_color is not None and use_color.has_key('defaults') and redirected:
                use_color=False
                
        log_obj=logger.QueueLogger
        log_obj=log_obj('','')
        reporter.g_rpter.Setup(
            log_obj,
            silent=SCons.Script.GetOption('silent'),
            verbose=SCons.Script.GetOption('verbose'),
            trace=SCons.Script.GetOption('trace'),
            use_color=use_color
            )
        
    def Start(self):
        reporter.verbose_msg("init","Starting up Parts")
        # setup variable
        self._setup_variables()
        # setup command line arguments
        self._setup_arguments()
        # setup default Enviroment overides
        self._setup_defenv()
        #try to setup all logger
        self._setup_logger()
        # generate help text
        if self.__build_mode=='help':
            self._setup_help_info()
        #setup the sdk options
        self._setup_sdk()
        #setup the progress meter
        self._setup_progress_meter()
        
        # setup managers
        self.part_manager=part_manager.part_manager()
        
        reporter.verbose_msg("init","Registering exit handler")
        atexit.register(self.ShutDown)
        
        
                
    def ShutDown(self):
        
        #get what went wrong if anything
        bf_lst=SCons.Script.GetBuildFailures()
        
        # write out data cache files..given nothing went wrong and 
        # we had soemthing to build
        
        # store our data
        targets=SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets != [] and SCons.Script.Main.exit_status == 0 and self.__build_mode=='build' and self.__use_cache == True:
            self.store_db_data() 
        
        
        #report what went wrong if anything
        if len(bf_lst) > 0:
            msg=''
            for bf in bf_lst:
                if common.is_list(bf.command):
                    cmd=' '.join(bf.command)
                else:
                    cmd=bf.command
                msg+=' Node: "%s"\n ' %(bf.node)
                #reporter.print_msg('Failed node: "%s"\n file: "%s" command: "%s"\n action: "%s"\n status: "%s"\n errstr: "%s"' %
                 #(bf.node,bf.filename,cmd,bf.action,bf.status,bf.errstr))
                #print bf.node.__dict__.keys()
##                tmp=''
##                for d in bf.node.sources:
##                    tmp+='    '+str(d)+"\n"
##                reporter.verbose_msg("error_summary","Source file for %s:\n%s"%(bf.node,tmp))
##                tmp=''
##                for d in bf.node.implicit:
##                    tmp+='    '+str(d)+"\n"
##                reporter.verbose_msg("error_summary","dependents file for %s:\n%s"%(bf.node,tmp))
            reporter.print_msg("Summary: %s build failure detected during build\n%s"%(len(bf_lst),msg))
        reporter.g_rpter.ShutDown()
        
    def Process(self,fs, options, targets, target_top):
        '''
        This does the main processing of the parts before Scons takes over again
        The main goal of this function to do an post Sconstruct reading processing 
        that we might want to do. such as processing the part files, 
        delayed mapping, etc
        '''
        
        targets=SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets == []:
            return 
        
        # generate the cache key
        self.generate_cache_key()
        
         #set stack info for reporting issues
        reporter.SetPartStackFrameInfo()
        
        # If the logger is not being used we want to get ride of the
        # queue logger to save memory
        if reporter.g_rpter.logger is logger.QueueLogger:
            # this should reset QueueLogger
            reporter.g_rpter.logger=logger.nil_logger
                    
        #process the Parts if any exist
        self.part_manager.ProcessParts()
                
        # process Queue
        self.parts_process_queue()        

        #clear the datacache
        datacache.ClearCache()
        
        #reset our statck info for error reporting.. (todo. double chack this again)
        reporter.ResetPartStackFrameInfo()
                
        
    
    ##
    
    def parts_process_queue(self):
       
        # process any data we have to post process
        if self.__post_process_queue!=[]:
            reporter.print_msg("Processing post logic queue")
            for i in self.__post_process_queue:
                i()
            self.__post_process_queue=[]
            reporter.print_msg("Done -- Processing post logic queue")
        
        #for p in self.part_manager.parts.values():
            #p.Env.subst(p.Env['ENV']['INCLUDE'])
            
    def map_known_nodes(self):
        '''
        This function maps all known node to the best Part object that it can.
        In some cases depending on layout of teh part and it sub part in relation
        to the source, a node might be added to more subpart that it should.
        However, since we only care to process a full Part ( and all it subpart)
        this does not break anything.
        
        The other item we do here ( as we are here already) is test the builder
        action for data that can be used to help detact a possible change in
        the build state. This build state is more global and as such will be stored
        latter in a more global data cache file.
        '''
        for drive in self.def_env.fs.Root.keys():
            if drive == '':
                continue
            for k,v in self.def_env.fs.Root[drive]._lookupDict.items():
                v.disambiguate()
                if isinstance(v,SCons.Node.FS.Dir) and v.env is None and getattr(v,'builder',None) is SCons.Node.FS.MkdirBuilder:
                    #this is most likely a Directory node that Scons would make 
                    # because some file would go in it
                    # it is not really need to map this to a Parts/Component
                    reporter.verbose_msg(["node_sorting"],v,"\033[1;32mSkipping directory")
                    pass
                ##need check for value nodes!!!!
                elif v.env is None and isinstance(v,SCons.Node.FS.File):
                    # this is some source file or implict dependance
                    # which mean I need to figure out who to give it to
                    ##need check
                    tmp=v.Dir('.')
                    while self.def_env.hasMetaTag(tmp,'owners','parts')==False:
                        if tmp == tmp.Dir('..'):
                            break;
                        else:
                            tmp=tmp.Dir('..')    
                    
                    tlst=self.def_env.MetaTagValue(tmp,'owners','parts',[])
                    if tlst ==[]:
                        reporter.verbose_msg(["node_sorting","node_sorting_failures"],v,"\033[1;31mMapping not found")
                        continue
                    for i in tlst:
                        self.part_manager.parts[i]._part_nodes.add(v)
                        reporter.verbose_msg("node_sorting",v,"mapped to \033[1;32m%s"%i)
                    
                    
                elif v.env is not None:
                    
                    
                    alias=v.env.get("PART_ALIAS",None)
                    if alias:
                        pobj=self.part_manager.parts[alias]
                        if v.has_builder():
                            add_builder_context_files(pobj,v.builder)
                        pobj._part_nodes.add(v)
                        reporter.verbose_msg("node_sorting",v,"\033[1;32m%s"%alias)
                    else:
                        reporter.verbose_msg(["node_sorting","node_sorting_failures"],v,"\033[1;31mhas no alias defined")
                        pass
                else:
                    reporter.verbose_msg(["node_sorting","node_sorting_failures"],v,"\033[1;31mMissed")
                    pass
                    
                # deal with the node build context
                #if v.has_builder():
                    #common.g_build_context_files.update(get_context_files(v))
                    
       
    def store_db_data(self):
        
        # store each part we know about information
        # call Part manager to do this
        reporter.print_msg("Storing Data Cache")
        
        # map known nodes
        self.map_known_nodes()
        # get data for Parts that we need to store
        alist,alias_set=self.part_manager.StoreCacheData()
        
        tmp={}
        if is_Sconstruct_up_to_date():
            tmp=datacache.GetCache("global_data")
            if tmp is None:
                tmp={}
        
        # store global data
        tmp1=tmp.get('known_aliases',set([]))
        tmp1.update(alias_set)
        global_data={
            'known_aliases':tmp1,
            'known_parts':common.extend_if_absent(tmp.get('known_parts',[]),alist)
            }
        
        # get SConstruct file data
        tmp={}
        for i in get_Sconstruct_files():
            i = self.def_env.File(i)
            tmp[i.path]={
                    'csig':i.get_csig(),
                    'timestamp':i.get_timestamp()
                    }
        global_data['sconstruct_files']=tmp
        
        #store data in Cache
        datacache.StoreData('global_data',global_data)       
        # save data
        st=time.time()
        datacache.SaveCache()
        print "store time=",time.time()-st
        reporter.print_msg("Done -- Storing Data Cache")
        

    #setup APIs
    def _setup_variables(self):
        ''' 
        Set all the varible that we have or need globally
        '''
        
        # set up the build mode
        args = sys.argv[1:]
        
        reporter.verbose_msg("startup","Setting building mode")
        if SCons.Script.GetOption('clean'):
            self.__build_mode='clean'
        elif SCons.Script.GetOption('help'):
            self.__build_mode='help'
        else:
            self.__build_mode='build'
            
        self.__use_cache=SCons.Script.GetOption("parts_cache")

        
            
    def _setup_defenv(self):
                
        org_env=SCons.Defaults._default_env        
        reporter.verbose_msg("startup","Creating default environment")
        env=core.generate_config({},{},{})
        env=env.Clone()
        env._CacheDir_path=None
        reporter.verbose_msg("startup","Resetting Scons default environment")
        tmp_queue=SCons.Defaults._default_env.get('PREPROCESS_LOGIC_QUEUE',[])
        self.def_env=SCons.Defaults._default_env=env
        self.def_env.Decider('MD5-timestamp')
        self.def_env['PREPROCESS_LOGIC_QUEUE']=self.__post_process_queue
        # setup other globals.. defaults
        reporter.verbose_msg("startup","Setting some global varibles needed in Default Environment")
        
        # turn off all default building of any items without a target, or until
        # default is called again to set one. ( ie the default by Scons is '.' which is everything)
        self.def_env.Default('')
        self.def_env.EnsureSConsVersion(1,2,0)
        
        
        
    def _setup_logger(self):
        
        reporter.verbose_msg("startup","Processing logger options")
        directory=self.def_env.Dir(self.def_env['LOG_ROOT_DIR'])
        log_obj=SCons.Script.GetOption('logger')
        
        #compatibility check
        if type(reporter.g_rpter.logger) is logger.QueueLogger:
            tmp=SCons.Script.ARGUMENTS.get('LOGGER',None)
            if tmp is not None:
                directory=self.def_env.Dir(self.def_env['LOG_ROOT_DIR'])
                tmp=self.def_env.subst(tmp)
                # remap old TEXT_LOGGER value
                if tmp=='TEXT_LOGGER':
                    tmp=self.def_env.subst('$'+tmp)

                    mod=load_module.load_module(
                        load_module.get_site_directories('loggers'),
                        tmp,
                        'logger')  
                    log_obj=mod.__dict__.get(tmp,logger.QueueLogger)
        
        #If the first try at this had nothing we have a Queue logger
        # to store everything we have to report so far
        if type(reporter.g_rpter.logger) is logger.QueueLogger:
            #Setup new log object and copy over stored messages
            log_obj=log_obj(directory.abspath,self.def_env['LOG_FILE_NAME'])
            reporter.g_rpter.reset_logger(log_obj)
        
    def _setup_arguments(self):
        '''
        Setup the main option with the varible that can be used to control it
        with SetOptionDefault or the config file
        '''
        
        overides={}
        tmp=SCons.Script.GetOption('target_platform')
        if tmp is not None:
            reporter.verbose_msg("startup","Setting target_platform:",tmp,'type:',type(tmp))
            overides['TARGET_PLATFORM']=tmp
        
        
        tmp=SCons.Script.GetOption('build_config')
        if tmp is not None:
            reporter.verbose_msg("startup","Setting build_config:",tmp,'type:',type(tmp))
            overides['CONFIG']=tmp
        
        tmp=SCons.Script.GetOption('tool_chain')
        if tmp is not None:
            reporter.verbose_msg("startup","Setting tool_chain:",tmp,'type:',type(tmp))
            overides['toolchain']=tmp
            
        tmp=SCons.Script.GetOption('mode')
        if tmp is not None:
            reporter.verbose_msg("startup","Setting mode:",tmp,'type:',type(tmp))
            overides['mode']=tmp

        tmp=SCons.Script.GetOption('ccopy_logic')
        if tmp is not None:
            reporter.verbose_msg("startup","Setting ccopy_logic:",tmp,'type:',type(tmp))
            overides['CCOPY_LOGIC']=tmp

        SCons.Script.ARGUMENTS.update(overides)
        
        # this is basically just tests code... 
        tmp=SCons.Script.GetOption('target_platform')
        reporter.trace_msg("target_platform_option","target_platform =",tmp)
        if tmp:
            reporter.trace_msg("target_platform_option_arch","target_arch =",tmp.ARCH)
            reporter.trace_msg("target_platform_option_os","target_os =",tmp.OS)
        
        reporter.trace_msg("build_config_option","build_config =",SCons.Script.GetOption('build_config'))
        reporter.trace_msg("tool_chain_option","tool_chain =",SCons.Script.GetOption('tool_chain'))
        reporter.trace_msg("mode_option","mode =",SCons.Script.GetOption('mode'))
        reporter.trace_msg("ccopy_logic_option","ccopy_logic =",SCons.Script.GetOption('ccopy_logic'))
        reporter.trace_msg("cfg_file_option","cfg_file =",SCons.Script.GetOption('cfg_file'))
        reporter.trace_msg("logger_option","logger =",SCons.Script.GetOption('logger'))
        reporter.trace_msg("show_progress_option","show_progress =",SCons.Script.GetOption('show_progress'))
        reporter.trace_msg("parts_cache_option","parts_cache =",SCons.Script.GetOption('parts_cache'))
        reporter.trace_msg("incremental_cache_option","incremental_cache =",SCons.Script.GetOption('incremental_cache'))
        reporter.trace_msg("incremental_dependent_checks_option","incremental_dependent_checks =",SCons.Script.GetOption('incremental_dependent_checks'))
        reporter.trace_msg("vcs_jobs_option","vcs_jobs =",SCons.Script.GetOption('vcs_jobs'))
        
    def _setup_sdk(self):
        return
        ##reporter.verbose_msg("startup","Processing SDK options")
##        csig,common.g_depends_data=core.load_depends_data()
##        #print common.g_depends_data
##        # first check to see if the main Sconstruct has changed
##        if csig != 0:
##            s=core.get_file_main_script(self.def_env)
##            if s != '':
##                fn=self.def_env.File(s)
##                # the the below passes we trust the database
##                #if fn.exists() and fn.get_csig()==csig:
##                #    setup_buildable_parts()
##        if self.def_env['use_source_for']!='' or self.def_env['use_sdk'] == True:
##            self.def_env['use_sdk'] = True
##            # get targets to build from source
##            reporter.g_rpter.part_message("Using prebuilt SDK's if they exist")
##            if self.def_env['use_source_for']!='':
##                src_targets=string.split(SCons.Script.ARGUMENTS['use_source_for'],',')
##            else:
##                src_targets=SCons.Script.COMMAND_LINE_TARGETS[:]
##            # create target list
##            setup_sdk_target_parts(src_targets)
##            add_dirty_parts(self.def_env)
##            reduce_target_alias_set(self.def_env)
##            create_sdk_set(self.def_env)

    def _setup_progress_meter(self):
        reporter.verbose_msg("startup","Setting up show-progress feature")
        if SCons.Script.GetOption('show_progress'):
            SCons.Script.Progress(self.def_env['PROGRESS_STR'],1,file=reporter.g_rpter.console,overwrite=True)
##            if self.def_env['HOST_OS'] == 'win32':
##                try:
##                    SCons.Script.Progress(self.def_env['PROGRESS_STR'],1,file=open('con:','w'),overwrite=True)
##                except Exception,ec:
##                    pass                
##            else:
##                try: 
##                    SCons.Script.Progress(self.def_env['PROGRESS_STR'],1,file=open('/dev/tty','w'),overwrite=True)
##                except Exception,ec:
##                    pass

    def add_preprocess_logic_queue(self,funcobj):
        self.__post_process_queue.append(funcobj)
                               


    def _setup_help_info(self):
        return
        import version_info,Variables
        reporter.verbose_msg("startup","In Help mode, setting up Help values")
        starttext='\n'+version_info.parts_version_text()+'''
Usage 'scons [scons options] [Parts options] [Targets]
Example: scons config=release foo

Use -H or --help-options for a list of scons options
'''
        cfg_files=[SCons.Script.GetOption('cfg_file')]
        vars=Variables.Variables(cfg_files,args=SCons.Script.ARGUMENTS)
        vars.AddVariables(*common.def_vars)
        SCons.Script.Help(starttext+vars.GenerateHelpText(self.def_env,True))

    def generate_cache_key(self):
        
            
        md5=hashlib.md5()        
                
        # get overides
        vars=copy.deepcopy(common.g_defaultoverides)        
        vars.update(SCons.Script.ARGUMENTS)
        # stuff that is getting mapped in more than one way
        # that needs to be white listed from being part of the chache key
        white_list=[
            'CONFIG',
            'config',
            'TARGET_PLATFORM',
            'toolchain',
            'tools',
            'mode',
            'CCOPY_LOGIC'
            ]
        for k,v in vars.items():
            if k not in white_list:
                tmp=get_content(v)
                md5.update(k+tmp )
                
        
        # list of arguments we want to process as they might effect build state
        args_to_process=[
            #'build_config', # get this from the def env
            'cfg_file',
            'file',
            'mode',
            'repository',
            'site_dir',
            #'tool_chain', # we use the different value to get a better match for this
            #'target_platform' # we get this from the def_env
        ]
        for k in args_to_process:
            v=SCons.Script.Main.OptionsParser.defaults[k]
            if v!=getattr(SCons.Script.Main.OptionsParser.values,k):
                tmp=get_content(v)
                md5.update(k+tmp)
                
                #print k,v,getattr(SCons.Script.Main.OptionsParser.values,k)            

        # this stuff makes up the core key
        md5.update("%s,%s,%s"%(self.def_env.subst('$CONFIG'),self.def_env['HOST_PLATFORM'],self.def_env['TARGET_PLATFORM']))
        # the thought is that the exact tool path are chached  
        # so changes to cli tools are seen as different
        for i in self.def_env['CONFIGURED_TOOLS']:
            tmp=self.def_env.get(i.upper())
            if tmp:
                md5.update(get_content(tmp))
            else:
                md5.update(i)
        # store the ENV value as this has value that can tell us of differences
        md5.update(get_content(self.def_env['ENV']))
        
        targets=SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp=target_type.target_type(t)
            if tmp.concept:
                md5.update(tmp.concept)
        
        self.__cache_key=md5.hexdigest()
        
    #state APIs
    @property
    def _cache_key(self):
        return self.__cache_key
    
    @property
    def _build_mode(self):
        return self.__build_mode
    
    @property
    def _part_manager(self,):
        return self.part_manager
    
   


common.AddVariable('use_source_for','','Controls what Part and dependents to build from source when building off of SDKs')
common.AddBoolVariable('use_sdk',False, 'Controls if SDKs dependents are used to build target instead of sources')

common.AddBoolVariable('use_env',False,'Controls if the shell enviroment will be used instead of values setup by SCons, and Parts')
common.AddBoolVariable('duplicate_build',False,'Controls if the src files are copied to the build area for building')
common.AddListVariable('mode',['default'],'Values used to control different build mode for a given part')

common.AddVariable('ALIAS_SEPARTATOR','::','seperator used to seperate namespace concepts from general alias value')

common.AddVariable('PROGRESS_STR',['scons: Evaluating |\r',
                                    'scons: Evaluating /\r',
                                    'scons: Evaluating -\r',
                                    'scons: Evaluating \\\r'],
                                    'What is used to show progress state')