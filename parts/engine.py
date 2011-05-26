import sys
import os
import stat
import atexit
import pprint
import hashlib
import copy
from cStringIO import StringIO

import SCons.Script    
import SCons.Node.FS

import glb
import common
import api.output
import errors
import logger
import poptions# want to remove
import load_module
import part_manager
import datacache
import target_type
import events
import pnode.pnode_manager




    
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
        api.output.verbose_msg("update_check",'No datacache For SConstruct file found')
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
                if glb.engine.def_env.File(i).get_csig() != tmp['csig']:
                    api.output.verbose_msg("update_check","File: %s has changed"%(i))
                    ret=False
        else:
            api.output.verbose_msg("update_check",'File: %s does not exist'%(i))
            ret=False
    
    return ret

    

###################
import types

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
        self.__def_env=None
        self.__post_process_queue=[]
        self.__cache_key=None
        self.__build_mode=None
        self.__had_error=None
        
        self._exit_up_to_date=False
        
        #events
        self.CacheDataEvent=events.Event()
        self.CacheDataEvent+=self._store_global_data
        
        # start up the reporter which controls the streams and all output
        use_color=SCons.Script.GetOption('use_color')
        # need to trace this before we set the colors else the tests break
        api.output.trace_msg("use_color_option","use_color =",use_color)
        redirected=os.isatty(sys.__stdout__.fileno()) ==False or os.isatty(sys.__stderr__.fileno()) ==False        
        if use_color is not None and use_color.has_key('defaults') and redirected:
                use_color=False
                
        log_obj=logger.QueueLogger
        log_obj=log_obj('','')
        glb.rpter.Setup(
            log_obj,
            silent=SCons.Script.GetOption('silent'),
            verbose=SCons.Script.GetOption('verbose'),
            trace=SCons.Script.GetOption('trace'),
            use_color=use_color
            )
            
        glb.pnodes=pnode.pnode_manager.manager()
        
    def Start(self):
        api.output.verbose_msg("init","Starting up Parts")
        # setup variable
        self._setup_variables()
        # setup command line arguments
        self._setup_arguments()
        # setup default Enviroment overides
        api.output.verbose_msg("startup","Creating default environment")
        SCons.Script.DefaultEnvironment()
        # turn off all default building of any items without a target, or until
        # default is called again to set one. ( ie the default by Scons is '.' which is everything)
        self.def_env.Default('')
        self.def_env.EnsureSConsVersion(1,2,0)
        #self._setup_defenv()
                
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
        self.__part_manager=part_manager.part_manager()
        
        api.output.verbose_msg("init","Registering exit handler")
        atexit.register(self.ShutDown)
        
        
                
    def ShutDown(self):
        
        # if we exit because we are up-to-date... just exit
        if self._exit_up_to_date:
            return
        
        #get what went wrong if anything
        bf_lst=SCons.Script.GetBuildFailures()
        
        # write out data cache files..given nothing went wrong and 
        # we had something to build
        
        # store our data
        targets=SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process, and that there are no error conditions
        if targets != [] and SCons.Script.Main.exit_status == 0 and self.HadError==False and self.__build_mode=='build' and self.__use_cache == True:
            # this event if for saving data that we only want saved, given a good build
            self.store_db_data(True) 
        else:
            self.store_db_data(False) 
        
        
        #report what went wrong if anything
        if len(bf_lst) > 0:
            msg=''
            for bf in bf_lst:
                if common.is_list(bf.command):
                    cmd=' '.join(bf.command)
                else:
                    cmd=bf.command
                msg+=' Node: "%s"\n ' %(bf.node)
                #api.output.print_msg('Failed node: "%s"\n file: "%s" command: "%s"\n action: "%s"\n status: "%s"\n errstr: "%s"' %
                 #(bf.node,bf.filename,cmd,bf.action,bf.status,bf.errstr))
                #print bf.node.__dict__.keys()
##                tmp=''
##                for d in bf.node.sources:
##                    tmp+='    '+str(d)+"\n"
##                api.output.verbose_msg("error_summary","Source file for %s:\n%s"%(bf.node,tmp))
##                tmp=''
##                for d in bf.node.implicit:
##                    tmp+='    '+str(d)+"\n"
##                api.output.verbose_msg("error_summary","dependents file for %s:\n%s"%(bf.node,tmp))
            api.output.print_msg("Summary: %s build failure detected during build\n%s"%(len(bf_lst),msg))
        glb.rpter.ShutDown()
        
    def UpToDateExit(self):
        # do a exit because everything is up-to-date
        self._exit_up_to_date=True
        # the question is what kind of exit to do.. hard or soft
        # Scons would preffer the soft.. however it looks like
        # state can get messed up here, so the hard case maybe better
        exit(0) # hard exit
        #self.def_env.Exit(0) # soft exit()
        
    def Process(self,fs, options, targets, target_top):
        '''
        This does the main processing of the parts before Scons takes over again
        The main goal of this function to do an post Sconstruct reading processing 
        that we might want to do. such as processing the part files, 
        delayed mapping, etc
        '''
        self.__had_error=False
        try:
            targets=SCons.Script.BUILD_TARGETS
            # check to see that we even have targets to process
            if targets == []:
                return 
            
            # generate the cache key
            self.generate_cache_key()
            
            #set stack info for reporting issues
            #errors.SetPartStackFrameInfo()
            
            # If the logger is not being used we want to remove the
            # queue logger to save memory
            if glb.rpter.logger is logger.QueueLogger:
                # this should reset QueueLogger
                glb.rpter.logger=logger.nil_logger
                        
            #process the Parts if any exist
            self.__part_manager.ProcessParts()
                    
            # process Queue
            self.parts_process_queue()        

            #clear the datacache
            datacache.ClearCache()
            
            #reset our stack info for error reporting.. (todo. double check this again)
            #errors.ResetPartStackFrameInfo()
        except:
            self.__had_error=True
            raise
                
        
    
    ##
    
    def parts_process_queue(self):
       
        # process any data we have to post process
        if self.__post_process_queue!=[]:
            api.output.print_msg("Processing post logic queue")
            total=len(self.__post_process_queue)*1.0
            cnt=0
            msg='{0}/{1}'.format(cnt,total)
            api.output.console_msg(" Processing post logic queue %3.2f%% %s \033[K"%((cnt/total*100),msg))
            for i in self.__post_process_queue:
                i()
                cnt+=1
                msg='{0}/{1} '.format(cnt,total)
                api.output.console_msg(" Processing post logic queue %3.2f%% %s \033[K"%((cnt/total*100),msg))
            msg='{0}/{1}'.format(cnt,total)
            api.output.console_msg(" Processing post logic queue %3.2f%% %s \033[K"%((cnt/total*100),msg))
            self.__post_process_queue=[]
            api.output.print_msg("Processing post logic queue finished!")
        
        #for p in self.__part_manager.parts.values():
            #p.Env.subst(p.Env['ENV']['INCLUDE'])
            
    def map_known_nodes(self):# remove this function if we can
        '''
        This function maps all known node to the best Part object that it can.
        In some cases depending on layout of the part and it sub part in relation
        to the source, a node might be added to more subpart that it should.
        However, since we only care to process a full Part ( and all it subpart)
        this does not break anything.
        
        The other item we do here ( as we are here already) is test the builder
        action for data that can be used to help detact a possible change in
        the build state. This build state is more global and as such will be stored
        latter in a more global data cache file.
        '''
        #st=time.time()
        #cnt=0
        #for drive in self.def_env.fs.Root.keys():
        #    if drive == '':
        #        continue
        #    for k,v in self.def_env.fs.Root[drive]._lookupDict.iteritems():
        #        v.disambiguate()
        #        cnt+=1
        #        if isinstance(v,SCons.Node.FS.Base):
        #            binfo=v.get_binfo()
        #            if not os.path.exists(v.path) and v.path != v.srcnode().path and\
        #                 binfo.bsourcesigs == [] and \
        #                    binfo.bdependsigs == [] and \
        #                    binfo.bimplicitsigs ==[]:   
        #                    # we need to store the variant directory
        #                    # as SCon does not store this. SCons assume this
        #                    # is fully mapped when it loads all the user data file
        #                    # after that point all data tests are safe to do
        #                    # we want to do this eailier than that to speed up the build
        #                    glb.engine.record_variant_source_mapping(v)
        #                    
                    
                #if isinstance(v,SCons.Node.FS.Dir) and v.env is None and getattr(v,'builder',None) is SCons.Node.FS.MkdirBuilder:
                #    #this is most likely a Directory node that Scons would make 
                #    # because some file would go in it
                #    # it is not really need to map this to a Parts/Component
                #    api.output.verbose_msg(["node_sorting"],v,"\033[1;32mSkipping directory")
                #    pass
                ###need check for value nodes!!!!
                #elif v.env is None and isinstance(v,SCons.Node.FS.File):
                #    # this is some source file or implict dependance
                #    # which mean I need to figure out who to give it to
                #    ##need check
                #    tmp=v.Dir('.')
                #    while self.def_env.hasMetaTag(tmp,'owners','parts')==False:
                #        if tmp == tmp.Dir('..'):
                #            break;
                #        else:
                #            tmp=tmp.Dir('..')    
                #    
                #    tlst=self.def_env.MetaTagValue(tmp,'owners','parts',[])
                #    if tlst ==[]:
                #        api.output.verbose_msg(["node_sorting","node_sorting_failures"],v,"\033[1;31mMapping not found")
                #        continue
                #    for i in tlst:
                #        self.__part_manager.parts[i]._part_nodes.add(v)
                #        api.output.verbose_msg("node_sorting",v,"mapped to \033[1;32m%s"%i)
                #    
                #    
                #elif v.env is not None:
                #    
                #    
                #    alias=v.env.get("PART_ALIAS",None)
                #    if alias:
                #        pobj=self.__part_manager.parts[alias]
                #        if v.has_builder():
                #            add_builder_context_files(pobj,v.builder)
                #        
                #        pobj._part_nodes.add(v)
                #        api.output.verbose_msg("node_sorting",v,"\033[1;32m%s"%alias)
                #    else:
                #        api.output.verbose_msg(["node_sorting","node_sorting_failures"],v,"\033[1;31mhas no alias defined")
                #        pass
                #else:
                #    api.output.verbose_msg(["node_sorting","node_sorting_failures"],v,"\033[1;31mMissed")
                #    pass
                    
                # deal with the node build context
                #if v.has_builder():
                    #glb.build_context_files.update(get_context_files(v))
        #print "Time for srcnode mapping", time.time() - st,cnt
       
    def store_db_data(self,goodexit):
        
        # map known nodes
        self.map_known_nodes()
        
        # store each part we know about information
        # call Part manager to do this
        api.output.print_msg("Storing Data Cache")
        st=time.time()
        self.CacheDataEvent(goodexit)
        api.output.verbose_msg(['cache_save'],"Fill time=",time.time()-st)
        st=time.time()
        datacache.SaveCache()
        api.output.verbose_msg(['cache_save'],"Save time=",time.time()-st)
        api.output.print_msg("Done -- Storing Data Cache")
        
    def _store_global_data(self,goodexit):
        # till I get the startup code better
        glb.pnodes.Store(goodexit)
        
        if goodexit:
            
            
            
            global_data={}
            ## get data for Parts that we need to store
            #get previous stored information as we may need it
            stored_data=datacache.GetCache('global_data')
            
        
            #tmp={}
            #if is_Sconstruct_up_to_date():
            #    tmp=datacache.GetCache("global_data")
            #    if tmp is None:
            #        tmp={}
            #
            ## store global data
            ## update known alias
            #tmp1=tmp.get('known_aliases',set([]))
            #tmp1.update(alias_set)
            #global_data={
            #    'known_aliases':tmp1,
            #    'known_parts':common.extend_if_absent(tmp.get('known_parts',[]),alist)
            #    }
        
            # get SConstruct file data ( maybe more than one )
            # we store a dictionary of
            #{<Sconstruct path w/name>:
            #       {
            #           csig:<value>
            #           timestamp:<value>
            #       }
            #}
            
            ## Store ninfo about the SConstruct file
            tmp={}
            for i in get_Sconstruct_files():
                i = self.def_env.File(i)
                tmp[i.path]={
                        'csig':i.get_csig(),
                        'timestamp':i.get_timestamp()
                        }
            #add to global data
            global_data['sconstruct_files']=tmp
            
            # store mapping info about "variant" source node.
            # these are generally source nodes that don't exist in the 
            # build variant directory because we told SCons to not copy them
            #tmp=self.__variant_source_mapping
            #global_data['variant_src_mapping']=tmp
            
            ### store the all know Aliases
            ## we need to filter out nodes that have stored binfo
            ## and did not build.. these need to stay unknown, until
            ## we try to build them
            #aliastostore= set() if stored_data is None else stored_data.get('aliases')
            #if aliastostore:
            #    tmp=filter(lambda x: x.isVisited, self.__aliases)
            #    aliastostore.update(tmp)
            #else:
            #    aliastostore=self.__aliases
            #global_data['aliases']=aliastostore  
            #
            #
            #valuestostore= {} if stored_data is None else stored_data.get('known_targets')
            #store_all=valuestostore == {}
            #for k,v in self.__known_targets.iteritems():
            #    if 'asdp' in k: print "&&&", k,v
            #    if v['node'].isVisited or store_all:
            #        del v['node']
            #        valuestostore[k]=v
            #        
            #
            #global_data['known_targets']=valuestostore
            
            #store data in Cache
            datacache.StoreData('global_data',global_data)       
        
        
    #def isKnownNode(self,strval):
    #    data=datacache.GetCache('global_data')
    #    if data is None:
    #        return False
    #    
    #    try:
    #        type=data['known_targets'][strval]
    #        return True
    #    except KeyError:
    #        return False
    #
    #def StoredNodeData(self,strval):
    #    data=datacache.GetCache('global_data')
    #    if data is None:
    #        return None
    #    
    #    try:
    #        return data['known_targets'][strval]
    #        
    #    except KeyError:
    #        return None
    #
    #    
    #def StringToNode(self,snode,ntype=None):
    #    data=datacache.GetCache('global_data')
    #    if data is None:
    #        return None
    #    
    #    stored_known_nodes=data['known_targets']
    #    
    #    if ntype is None:
    #        try:
    #            type=stored_known_nodes[snode]['_type_']
    #        except KeyError:
    #            type='entry'
    #            
    #    if type == 'File':
    #        return self.def_env.File(snode)
    #    elif type == 'Dir':
    #        return self.def_env.Dir(snode)
    #    elif type == 'Entry':
    #        return self.def_env.Entry(snode)
    #    elif type == 'Value':
    #        return self.def_env.Value(snode)
    #    elif type == 'Alias':
    #        stored_known_alias=data['aliases']
    #        try:
    #            info=stored_known_alias[snode]
    #        except KeyError:
    #            info=None
    #        node = self.def_env.Alias(snode)[0]
    #        if binfo:
    #            node._memo['get_stored_info']=info
    #        return node
    #    return None
    #        
        

    #setup APIs
    def _setup_variables(self):
        ''' 
        Set all the varible that we have or need globally
        '''
        
        # set up the build mode
        args = sys.argv[1:]
        
        api.output.verbose_msg("startup","Setting building mode")
        if SCons.Script.GetOption('clean'):
            self.__build_mode='clean'
        elif SCons.Script.GetOption('help'):
            self.__build_mode='help'
        else:
            self.__build_mode='build'
            
        self.__use_cache=SCons.Script.GetOption("parts_cache")

        
            
    def _setup_defenv(self):
                
        #import settings
        ##org_env=SCons.Defaults._default_env        
        #env=settings.DefaultSettings().Environment().Clone()
        ##env._CacheDir_path=None
        ##api.output.verbose_msg("startup","Resetting Scons default environment")
        #self.def_env=SCons.Defaults._default_env=env
        #self.def_env['PREPROCESS_LOGIC_QUEUE']=self.__post_process_queue
        pass

    
    def _setup_logger(self):
        
        api.output.verbose_msg("startup","Processing logger options")
        directory=self.def_env.Dir(self.def_env['LOG_ROOT_DIR'])
        log_obj=SCons.Script.GetOption('logger')
        
        #compatibility check
        if type(glb.rpter.logger) is logger.QueueLogger:
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
        if type(glb.rpter.logger) is logger.QueueLogger:
            #Setup new log object and copy over stored messages
            log_obj=log_obj(directory.abspath,self.def_env['LOG_FILE_NAME'])
            glb.rpter.reset_logger(log_obj)
        
    def _setup_arguments(self):
        '''
        Setup the main option with the varible that can be used to control it
        with SetOptionDefault or the config file
        '''
        
        overides={}
        tmp=SCons.Script.GetOption('target_platform')
        if tmp is not None:
            api.output.verbose_msg("startup","Setting target_platform:",tmp,'type:',type(tmp))
            overides['TARGET_PLATFORM']=tmp
        
        
        tmp=SCons.Script.GetOption('build_config')
        if tmp is not None:
            api.output.verbose_msg("startup","Setting build_config:",tmp,'type:',type(tmp))
            overides['CONFIG']=tmp
        
        tmp=SCons.Script.GetOption('tool_chain')
        if tmp is not None:
            api.output.verbose_msg("startup","Setting tool_chain:",tmp,'type:',type(tmp))
            overides['toolchain']=tmp
            
        tmp=SCons.Script.GetOption('mode')
        if tmp is not None:
            api.output.verbose_msg("startup","Setting mode:",tmp,'type:',type(tmp))
            overides['mode']=tmp

        tmp=SCons.Script.GetOption('ccopy_logic')
        if tmp is not None:
            api.output.verbose_msg("startup","Setting ccopy_logic:",tmp,'type:',type(tmp))
            overides['CCOPY_LOGIC']=tmp

        SCons.Script.ARGUMENTS.update(overides)
        
        # this is basically just tests code... 
        tmp=SCons.Script.GetOption('target_platform')
        api.output.trace_msg("target_platform_option","target_platform =",tmp)
        if tmp:
            api.output.trace_msg("target_platform_option_arch","target_arch =",tmp.ARCH)
            api.output.trace_msg("target_platform_option_os","target_os =",tmp.OS)
        
        api.output.trace_msg("build_config_option","build_config =",SCons.Script.GetOption('build_config'))
        api.output.trace_msg("tool_chain_option","tool_chain =",SCons.Script.GetOption('tool_chain'))
        api.output.trace_msg("mode_option","mode =",SCons.Script.GetOption('mode'))
        api.output.trace_msg("ccopy_logic_option","ccopy_logic =",SCons.Script.GetOption('ccopy_logic'))
        api.output.trace_msg("cfg_file_option","cfg_file =",SCons.Script.GetOption('cfg_file'))
        api.output.trace_msg("logger_option","logger =",SCons.Script.GetOption('logger'))
        api.output.trace_msg("show_progress_option","show_progress =",SCons.Script.GetOption('show_progress'))
        api.output.trace_msg("parts_cache_option","parts_cache =",SCons.Script.GetOption('parts_cache'))
        api.output.trace_msg("incremental_cache_option","incremental_cache =",SCons.Script.GetOption('incremental_cache'))
        api.output.trace_msg("incremental_dependent_checks_option","incremental_dependent_checks =",SCons.Script.GetOption('incremental_dependent_checks'))
        api.output.trace_msg("vcs_jobs_option","vcs_jobs =",SCons.Script.GetOption('vcs_jobs'))
        api.output.trace_msg("update_option","update =",SCons.Script.GetOption('update'))
        
    def _setup_sdk(self):
        return
        ##api.output.verbose_msg("startup","Processing SDK options")
##        csig,glb.depends_data=core.load_depends_data()
##        #print glb.depends_data
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
##            glb.rpter.part_message("Using prebuilt SDK's if they exist")
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
        api.output.verbose_msg("startup","Setting up show-progress feature")
        if SCons.Script.GetOption('show_progress'):
            SCons.Script.Progress(self.def_env['PROGRESS_STR'],1,file=glb.rpter.console,overwrite=True)

    def add_preprocess_logic_queue(self,funcobj):
        self.__post_process_queue.append(funcobj)
                               


    def _setup_help_info(self):
        return
        import version_info,Variables
        api.output.verbose_msg("startup","In Help mode, setting up Help values")
        starttext='\n'+version_info.parts_version_text()+'''
Usage 'scons [scons options] [Parts options] [Targets]
Example: scons config=release foo

Use -H or --help-options for a list of scons options
'''
        cfg_files=[SCons.Script.GetOption('cfg_file')]
        vars=Variables.Variables(cfg_files,args=SCons.Script.ARGUMENTS)
        vars.AddVariables(*common.def_vars)
        SCons.Script.Help(starttext+vars.GenerateHelpText(self.def_env,True))

    def record_variant_source_mapping(self,node):
        self.__variant_source_mapping[node.path]=node.srcnode().path

    def get_variant_source_mapping(self,nodestr):
        try:
            return self.__variant_source_mapping[nodestr]
        except KeyError:
            tmp=datacache.GetCache("global_data")
            if tmp:
                tmpval=tmp.get('variant_src_mapping',{})
                tmpval.update(self.__variant_source_mapping)
                self.__variant_source_mapping=tmpval
                if not self.__variant_source_mapping.has_key(nodestr):
                    self.__variant_source_mapping[nodestr]=None
        return self.__variant_source_mapping[nodestr]
                
                

    def generate_cache_key(self):
        
            
        md5=hashlib.md5()        
                
        # get overides
        vars={}
        #vars=copy.deepcopy(glb.defaultoverides)        
        vars.update(SCons.Script.ARGUMENTS)
        # stuff that is getting mapped in more than one way
        # that needs to be white listed from being part of the cache key
        white_list=[
            'CONFIG',
            'config',
            'TARGET_PLATFORM',
            'toolchain',
            'tools',
            'mode',
            'CCOPY_LOGIC',
            'BUILD_BRANCH'
            ]
        for k,v in vars.iteritems():
            if k not in white_list:
                tmp=common.get_content(v)
                md5.update(k+tmp )
                
        
        # list of arguments we want to process as they might effect build state
        args_to_process=[
            #'build_config', # get this from the def env
            'cfg_file',
            'file',
            'mode',
            'repository',
            'site_dir'
            #'tool_chain', # we use the different value to get a better match for this
            #'target_platform' # we get this from the def_env
        ]
        for k in args_to_process:
            v=SCons.Script.Main.OptionsParser.defaults[k]
            if v!=getattr(SCons.Script.Main.OptionsParser.values,k):
                tmp=common.get_content(v)
                md5.update(k+tmp)
                
                #print k,v,getattr(SCons.Script.Main.OptionsParser.values,k)            

        # this stuff makes up the core key
        md5.update("%s,%s,%s"%(self.def_env.subst('$CONFIG'),self.def_env['HOST_PLATFORM'],self.def_env['TARGET_PLATFORM']))
        # the thought is that the exact tool path are chached  
        # so changes to cli tools are seen as different
        for i in self.def_env['CONFIGURED_TOOLS']:
            tmp=self.def_env.get(i.upper())
            if tmp:
                md5.update(common.get_content(tmp))
            else:
                md5.update(i)
        # store the ENV value as this has value that can tell us of differences
        md5.update(common.get_content(self.def_env['ENV']))
        
        targets=SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp=target_type.target_type(t)
            md5.update(tmp.Section)
        
        self.__cache_key=md5.hexdigest()
        
    #state APIs
    #def add_to_known_targets(self, tlist,pobj):
    #    for t in tlist:
    #        #SCons does not like having duplicate Target nodes
    #        # given this we know we should only see it once
    #        # however we still want to record information 
    #        # for items using the Parts allow_duplicates feature
    #        alias=pobj.Alias
    #        section=pobj.DefiningSection.Env['PART_SECTION']
    #        if isinstance(t,SCons.Node.FS.File):
    #            type='File'
    #            key=t.path
    #        elif isinstance(t,SCons.Node.FS.Dir):
    #            type='Dir'
    #            key=t.path
    #        elif isinstance(t,SCons.Node.FS.Entry):
    #            type='Entry'
    #            key=t.path
    #        elif isinstance(t,SCons.Node.Alias.Alias):
    #            type='Alias'
    #            key=t.name
    #        elif isinstance(t,SCons.Node.Python.Value):
    #            type='Value'
    #            key=t.value
    #        else:
    #            pass
    #        try:
    #            self.__known_targets[key]['_type']=type
    #            self.__known_targets[key]['node']=t
    #            try:
    #                self.__known_targets[key][alias].add(section)
    #            except KeyError:
    #                self.__known_targets[key][alias]=set([section])
    #        except KeyError:
    #            self.__known_targets[key]={
    #                        alias:set([section]),
    #                        '_type':type,
    #                        'node':t
    #                        }
    #        
    #        if isinstance(t,SCons.Node.FS.File) or isinstance(t,SCons.Node.FS.Dir):
    #            dnode=t.Dir('.')
    #                    
    #            while True:
    #                try:
    #                    if alias in self.__known_targets[dnode.path].keys():
    #                        return
    #                except KeyError:
    #                    pass
    #                try:
    #                    self.__known_targets[dnode.path]['_type']='dir'
    #                    self.__known_targets[dnode.path]['node']=dnode
    #                    try:
    #                        self.__known_targets[dnode.path][alias].add(section)
    #                    except KeyError:
    #                        self.__known_targets[dnode.path][alias]=set([section])
    #                except KeyError:
    #                    self.__known_targets[dnode.path]={
    #                                alias:set([section]),
    #                                '_type':'dir',
    #                                'node':dnode
    #                                }
    #                if dnode == dnode.Dir('..'):
    #                    return
    #                dnode=dnode.Dir('..')
    #            
    #                
    #
    #def AddAlias(self,data):
    #    self.__aliases.update(data)
    #    
    #@property
    #def Aliases(self):
    #    return self.__aliases
    #
    @property
    def _cache_key(self):
        if self.__cache_key is None:
            self.generate_cache_key()
        return self.__cache_key
    
    @_cache_key.setter
    def _cache_key(self,val):
        self.__cache_key=val
    
    @property
    def _build_mode(self):
        return self.__build_mode
    
    @property
    def _part_manager(self,):
        return self.__part_manager
    
    @property
    def HadError(self):
        if self.__had_error is None:
            SCons.Script.Main.exit_status=2
            return True
            
        return self.__had_error
    
    @HadError.setter
    def HadError(self,value):
        self.__had_error=value
   
    @property                
    def def_env(self):
        return self.__def_env
    
    @def_env.setter
    def def_env(self,value):
        self.__def_env=SCons.Defaults._default_env=value
        # do some tweak that we seem to need for default environments
        self.__def_env._CacheDir_path=None
        #This is backward compatibility for Parts
        self.__def_env['PREPROCESS_LOGIC_QUEUE']=self.__post_process_queue
        
        self.def_env.Decider('MD5-timestamp')
        
                

api.register.add_variable('use_source_for','','Controls what Part and dependents to build from source when building off of SDKs')
api.register.add_bool_variable('use_sdk',False, 'Controls if SDKs dependents are used to build target instead of sources')

api.register.add_bool_variable('use_env',False,'Controls if the shell enviroment will be used instead of values setup by SCons, and Parts')
api.register.add_bool_variable('duplicate_build',False,'Controls if the src files are copied to the build area for building')
api.register.add_list_variable('mode',['default'],'Values used to control different build mode for a given part')

api.register.add_variable('ALIAS_SEPARTATOR','::','seperator used to seperate namespace concepts from general alias value')

api.register.add_variable('PROGRESS_STR',['scons: Evaluating |\r',
                                    'scons: Evaluating /\r',
                                    'scons: Evaluating -\r',
                                    'scons: Evaluating \\\r'],
                                    'What is used to show progress state')
