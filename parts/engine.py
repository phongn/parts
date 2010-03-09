
import common
import reporter
import logger
import poptions
import core

import SCons.Script    

import sys
import atexit


###
## move all this when we redo the SDK option

def target_to_alias(target,ret):    
    ''' This function will make the target to the set of alias that map to it'''
    # test to make sure we data to read from.
    if common.g_depends_data != {}:
        #Iterate the dictionay
        for k,v in common.g_depends_data.iteritems():
            # see if the target we want exists in this parts target set
            if target in v['targets']:
                # if so we want to make sure we don't already have it 
                # this prevents a stack overflow as we will recurse.
                if k not in ret:
                    # since it is not in the list we will add it
                    ret.add(k)
                    # we call this function to add any other mappings
                    ## not sure at this point if it is really need any more
                    ## but i don't want to remove it as it is not breaking anything
                    ## by existing ... need to remember why it was needed
                    target_to_alias(k,ret)
                #also test to see if this is a subpart
                # if so we need to add the root part alias as well
                if v['root_part']!=k:
                    ret.add(v['root_part'])
                
    return ret

def _expand(target):
    for j in common.g_depends_data[target]['depends']:
        if common.g_depends_data[j]['root_part']!=j:
            if common.g_depends_data[j]['root_part'] not in common.g_buildable_part:
                common.g_buildable_part.add(common.g_depends_data[j]['root_part'])
                _expand(common.g_depends_data[j]['root_part'])
        common.g_buildable_part.add(j)
        
def setup_buildable_parts():
    ''' this sets up a list of stuff we know we need to build'''
    alst=set()
    for t in SCons.Script.BUILD_TARGETS:
        alst=target_to_alias(t,set())
        if alst==set():
            common.g_buildable_part=set()
            return
        else:
            common.g_buildable_part|=alst
            for i in alst:
                _expand(i)
    #print "common.g_buildable_part=",common.g_buildable_part      

def setup_sdk_target_parts(lst):
    '''
    This function will set up the initial set of part we want to target to 
    be built form source code
    ''' 
    # need def env to for the reporter object
    def_env=SCons.Script.DefaultEnvironment()
    #For each item passed in we need to get the alias set
    # this alias set is teh set of alias we will see when we read a part file
    # this value is what we key off of to know what to do when we read a given Part
    for t in lst:
        #get the alias set
        alst=target_to_alias(t,set())
        # if this set is empty we don't have this target in the DB file we made
        if alst==set():
            # if this is not the a base set of aliases
            # we make to build everything ( test below is incomplete)
            if t !='all' and t!='.':
                # we want to report that we don't know this target.. to help latter if we ahve a big problem
                def_env['PARTS_REPORTER'].part_message("Skipping "+t+" as source target as we don't have it in the database")
            pass
        else:
            # given that it is not empty, add the set to the set we have already.
            common.g_target_alias|=alst
            
            
def add_dirty_parts(def_env):
    ''' This function test to see if the part file has changed. If this is so 
    then we want to force this to be built via source. We need to also test
    to make sure the SDK file exists, else we build via source. We assume that 
    if the SDK exists here and the parts file doesn't that it is not dirty'''
    if common.g_buildable_part == set():
        # we try looking at all preknown parts for DB
        tmp=common.g_depends_data.keys()
    else:
        # we try looking at all known parts we need to build
        tmp=common.g_buildable_part
        
    for i in tmp:
        sdk_exists=os.path.exists(common.g_depends_data[i].get('sdk_file','#_no_FILe_'))
        file_exists=os.path.exists(common.g_depends_data[i]['file_name'])
        make_sdk=common.g_depends_data[i]['make_sdk']
        # test to see if "src" parts file exists
        if file_exists:
            # so we need to test it csig value with our stored one
            csig=common.g_depends_data[i]['csig']
            # make the file object to get the csig value.
            ## NOTE!! we don't use it to test existance because of bug that happens in
            ## SCons that prevents the checking out of the code in parts to work corectly
            fn=def_env.File(common.g_depends_data[i]['file_name'])
            
            # if the csig value or the SDK file we have stored are bad we need to
            # buidl this from source
            if csig!=fn.get_csig() or sdk_exists==False:
                common.g_target_alias.add(i)
                # might be a hack .. but allow these part to be fully built
                # useful in cases of subpart in which the root part just call
                # subpart but does not depend on them, or the target we are building
                # does not depend on the root part only a sub-part. This would prevent
                # root parts SDK file from being made. the below forces that "part" to
                # be built, so it the SDK is created
                ## the make_sdk test prevents unit_tests from being built as they
                ## don't affect the SDK output.
                if i not in SCons.Script.BUILD_TARGETS and make_sdk:
                    SCons.Script.BUILD_TARGETS.append(i)
        elif sdk_exists==True and file_exists == False:
            # in this case we assume the SDK file is up todate.
            continue
        else: 
            common.g_target_alias.add(i)
                    
def reduce_target_alias_set(def_env):
    ret=set()
    cc=common.g_target_alias.copy()
    
    # for each item in the list we target to build from source
    for i in cc:
        # the dependd of this part
        depends=common.g_depends_data[i]['depends']
        # test to if any of the targets we have depend on this target depends list
        for n in common.g_target_alias:
            if n in depends:
                # if so we break and not add it to the reduce set
                break
        else:
            # if we are here we did not depend on it, so we know this is a base 
            # node we have to build it....
            ret.add(i)
            # if this is a root part we want to add the sub parts it depends on
            # this is to get around issue of optional subparts that would make 
            # the SDK incomplete.
            if common.g_depends_data[i]['root_part'] == i:
                for n in depends:
                    if common.g_depends_data[n]['root_part'] == i:
                        ret.add(n)
            
            
    common.g_target_alias=set(ret)
    def_env['PARTS_REPORTER'].part_message("Reduce set to build from source "+str(common.g_target_alias))
    
def create_sdk_set(def_env):
    ret=set()

    if common.g_buildable_part == set():
        # we try looking at all preknown parts for DB
        tmp=common.g_depends_data.keys()
    else:
        # we try looking at all known parts we need to build
        tmp=common.g_buildable_part

    # for each item in the buildable part set
    for k in tmp:
        # get the depend set
        v=common.g_depends_data[k]
        # loop to see if targets we have to build from source
        # depends on the buildable items depends list
        for a in common.g_target_alias:
            if a in v['depends'] or k in common.g_target_alias:
                # if so we break, as we don't want to add this
                # to the build from SDK set
                break
        else:
            # we want to add this to the build from SDK set
            # only add root parts, as currently we don't want to mix part build as part src and SDK
            if v['root_part']==k:
                ret.add(k)
    
    common.g_build_as_sdk=ret
    def_env['PARTS_REPORTER'].part_message("Set to try to build as SDK "+str(common.g_build_as_sdk))
    
################################################################################




# would it be nice if ther was a addon base in Scons... hmmmmm
class parts_addon(object):
    def __init__(self):
        # start up the reporter which controls the streams and all output
        log_obj=logger.QueueLogger
        log_obj=log_obj('','')#(directory.abspath,env['LOG_FILE_NAME'])
        reporter.g_rpter=reporter.reporter(
            log_obj,
            SCons.Script.GetOption('silent'),
            SCons.Script.GetOption('verbose')
            )
        reporter.verbose_msg("init","Starting up Parts")
        
        reporter.verbose_msg("init","Registering exit handler")
        atexit.register(self.ShutDown)
        
    def Start(self):
               
        # setup variable
        self.setup_variables()
        # setup command line arguments
        self.setup_arguments()
        # setup default Enviroment overides
        self.setup_defenv()
        #try to setup all logger
        self.setup_logger()
        # generate help text
        if self.BuildMode=='help':
            self.setup_help_info()
        #setup the sdk options
        self.setup_sdk()
        #setup the progress meter
        self.setup_progress_meter()
                
    def ShutDown(self):
        
        bf_lst=SCons.Script.GetBuildFailures()
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

    #setup APIs
    def setup_variables(self):
        ''' 
        Set all the varible that we have or need globally
        '''
        
        # set up the build mode
        args = sys.argv[1:]
        
        reporter.verbose_msg("startup","Setting building mode")
        if SCons.Script.GetOption('clean'):
            common.g_part_mode='clean'
        elif SCons.Script.GetOption('help'):
            common.g_part_mode='help'
        else:
            common.g_part_mode='build'

        
            
    def setup_defenv(self):
                
        reporter.verbose_msg("startup","Creating default environment")
        env=core.generate_config({},{},{})
        env=env.Clone()
        env._CacheDir_path=None
        reporter.verbose_msg("startup","Resetting Scons default environment")
        self.def_env=SCons.Defaults._default_env=env
        self.def_env.Decider('MD5-timestamp')
         ## setup other globals.. defaults
        reporter.verbose_msg("startup","Setting some global varibles needed in Defafult Environment")
        self.def_env['PARTS_REPORTER']=reporter.g_rpter
        # need to handle more complete subst mapper handling
        self.def_env["PARTS_COMPLEX_SUB"]=0
        # needed for Dependon and other preprocessing logic (like setting rpaths)
        self.def_env['PREPROCESS_LOGIC_QUEUE']=[]
        # turn off all default building of any items without a target, or until
        # default is called again to set one. ( ie the default by Scons is '.' which is everything)
        self.def_env.Default('')
        self.def_env.EnsureSConsVersion(1,2,0)
        
        
        
    def setup_logger(self):
        
        reporter.verbose_msg("startup","Processing logger options")
        directory=self.def_env.Dir(self.def_env['LOG_ROOT_DIR'])
        log_obj=SCons.Script.GetOption('logger')
        
        #If the first try at this had nothing we have a Queue logger
        # to store everything we have to report so far
        if type(reporter.g_rpter.logger) is logger.QueueLogger:
            #Setup new log object and copy over stored messages
            log_obj=log_obj(directory.abspath,self.def_env['LOG_FILE_NAME'])
            reporter.g_rpter.reset_logger(log_obj)
        
    def setup_arguments(self):
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
        
        
    def setup_sdk(self):
        reporter.verbose_msg("startup","Processing SDK options")
        csig,common.g_depends_data=core.load_depends_data()
        #print common.g_depends_data
        # first check to see if the main Sconstruct has changed
        if csig != 0:
            s=core.get_file_main_script(self.def_env)
            if s != '':
                fn=self.def_env.File(s)
                # the the below passes we trust the database
                #if fn.exists() and fn.get_csig()==csig:
                #    setup_buildable_parts()
        if self.def_env['use_source_for']!='' or self.def_env['use_sdk'] == True:
            self.def_env['use_sdk'] = True
            # get targets to build from source
            reporter.g_rpter.part_message("Using prebuilt SDK's if they exist")
            if self.def_env['use_source_for']!='':
                src_targets=string.split(SCons.Script.ARGUMENTS['use_source_for'],',')
            else:
                src_targets=SCons.Script.COMMAND_LINE_TARGETS[:]
            # create target list
            setup_sdk_target_parts(src_targets)
            add_dirty_parts(self.def_env)
            reduce_target_alias_set(self.def_env)
            create_sdk_set(self.def_env)

    def setup_progress_meter(self):
        reporter.verbose_msg("startup","Setting up show-progress feature")
        if SCons.Script.GetOption('show_progress'):
            if self.def_env['HOST_OS'] == 'win32':
                try:
                    SCons.Script.Progress(self.def_env['PROGRESS_STR'],1,file=open('con:','w'),overwrite=True)
                except Exception,ec:
                    pass                
            else:
                try: 
                    SCons.Script.Progress(self.def_env['PROGRESS_STR'],1,file=open('/dev/tty','w'),overwrite=True)
                except Exception,ec:
                    pass
    
    def setup_help_info(self):
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
    
    #state APIs
    
    def BuildMode(self):
        return common.g_build_mode
    
    
    
    

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