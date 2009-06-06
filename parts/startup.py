'''
The startup configuration code
'''

import SCons.Script
import config
import common
import core
import sdk
import exportitem
import installs
import logger
import reporter
import platform_info
import os
import string


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

def start():
    '''This function sets up all the data and objects needed to have everything work correctly'''
    # start off looking for options that we need to display extra data on
    def_env=SCons.Script.DefaultEnvironment()    
    
    import sys
    args = sys.argv[1:]
    if SCons.Script.GetOption('clean'):
        common.g_part_mode='clean'
    elif SCons.Script.GetOption('help'):
        common.g_part_mode='help'
        #core.generate_help_text()
    else:
        common.g_part_mode='build'
        
    # options for dumping information about configurations
    list_tool=SCons.Script.ARGUMENTS.get('list_tool',None)

    if list_tool!=None:
        if list_tool=='all':
            config.dump_config_list()
        else:
            config.dump_config_list(list_tool)
        SCons.Script.Exit(0)
        
    verbose=SCons.Script.GetOption('verbose')
    if verbose!=None:
        print 'verbose not implemented yet'

    ## setup the command arguments
    init_args() 
    env=core.generate_config({},{},{'tool_chain':[]})
    
    ## setup the reporter so we have a way to consitantly output and manage data
      
    log_obj=env['LOGGER']
    if common.is_string(log_obj)==True:
        log_obj=env.get(log_obj,logger.nil_logger)
    directory=def_env.Dir(env['LOG_ROOT_DIR'])
    log_obj=log_obj(directory.abspath,env['LOG_FILE_NAME'])
    rpt=reporter.reporter(log_obj,def_env.GetOption('silent'),env['STREAM_WARNING_AS_ERROR'])
    
    ## setup other globals.. defaults
    
    def_env['PARTS_REPORTER']=rpt
    # need to handle more complete subst mapper handling
    def_env["PARTS_COMPLEX_SUB"]=0
    # needed for Dependon and other preprocessing logic (like setting rpaths)
    def_env['PREPROCESS_LOGIC_QUEUE']=[]

    ##load cached data
    csig,common.g_depends_data=core.load_depends_data()
    #print common.g_depends_data
    # first check to see if the main Sconstruct has changed
    if csig != 0:
        s=core.get_file_main_script(def_env)
        if s != '':
            fn=def_env.File(s)
            # the the below passes we trust the database
            if fn.exists() and fn.get_csig()==csig:
                setup_buildable_parts()
    if env['use_source_for']!='' or env['use_sdk'] == True:
        env['use_sdk'] = True
        # get targets to build from source
        rpt.part_message("Using prebuilt SDK's if they exist")
        if env['use_source_for']!='':
            src_targets=string.split(SCons.Script.ARGUMENTS['use_source_for'],',')
        else:
            src_targets=SCons.Script.COMMAND_LINE_TARGETS[:]
        # create target list
        setup_sdk_target_parts(src_targets)
        add_dirty_parts(def_env)
        reduce_target_alias_set(def_env)
        create_sdk_set(def_env)
    print env['TARGET_PLATFORM']
    # turn off all default building of any items without a target, or until
    # default is called again to set one. ( ie the default by Scons is '.' which is everything)
    def_env.Default('')
    def_env.EnsureSConsVersion(0,98,0)#'0x0d20070918')
    
    SCons.Script.Decider('MD5-timestamp')
    # this logic may not be 100% correct
    if env['show_progress']:
        if def_env['PLATFORM'] == 'win32':
            SCons.Script.Progress(env['PROGRESS_STR'],1,file=open('con:','w'),overwrite=True)
        else:
            try: 
                SCons.Script.Progress(env['PROGRESS_STR'],1,file=open('/dev/tty','w'),overwrite=True)
            except Exception,ec:
                pass
            
    


def init_args():
    '''
    the idea here is to map option in the form of -- to the varibles. This is only
    needed for a few items, that arguably cross a line between -- and key=val such as config
    '''
    #''' Since the Option class does not work as we would like, we hard code some logic for the time being
    #This current revision loops over the options that have been set in def_args. Going forward we will still
    #want to see what we can do to clean this up even more.
    #'''
    #start setup of the arguments    

##    #for kv in def_args.items():
##    #    common.g_args[kv[0]]=kv[1]
##    common.g_args.update(common.def_args)
##
##    ### Load config file ######    
##    # Next get the config file settings, if any
##    cfg_file=SCons.Script.GetOption('cfg_file')
##    #SCons.Script.ARGUMENTS.get('cfg_file',common.g_args['cfg_file'])
##    
##    # if we have a config file, load those values
##    d1={}
##    if os.path.exists(cfg_file):
##        print 'Loading config file [',cfg_file,']'
##        execfile(cfg_file, d1,common.g_args)
##    elif cfg_file!='parts.cfg':
##        print "PARTS: Warning - cfg_file =",cfg_file,"was not found! Ignoring file..."
##        

    ### override with any command line arguments #####
    
##    # set the preferred tools
##    lst=[]
##    if SCons.Script.ARGUMENTS.has_key('tool_chain'):
##        lst=string.split(SCons.Script.ARGUMENTS['tool_chain'],',')
##    else:
##        lst=common.g_args['tool_chain']
##    common.g_args['tool_chain']=common.process_tool_arg(lst)
##        
##    if SCons.Script.ARGUMENTS.has_key('mode'):
##        common.g_args['mode']=string.split(SCons.Script.ARGUMENTS['mode'],',')
##    else:
##        common.g_args['mode']=common.g_args['mode']
##    
####    # this value can't be overridden via SetDefaultOptions
####    del common.def_args['cfg_file']
##    # these can so i need to add these back in latter so SetDefault works
##    # might want to rethink how SetDefault work latter as well.
##    tools_tmp = common.def_args['tool_chain']
##    mode_tmp = common.def_args['mode']
##    
##    del common.def_args['tool_chain']
##    del common.def_args['mode']
##    
##    common.g_args['config']=SCons.Script.ARGUMENTS.get('config',
##            common.g_args.get('config',common.g_args['default_config'])
##            )
##
##    for key in common.def_args.keys():
##        if common.is_bool(common.g_args[key]):
##            common.g_args[key]=common.option_bool(SCons.Script.ARGUMENTS.get(key,common.g_args[key]),key,common.g_args[key])
##        else:
##            common.g_args[key]=SCons.Script.ARGUMENTS.get(key,common.g_args[key])
##    
##    common.def_args['tool_set']=tools_tmp
##    common.def_args['mode']=mode_tmp
##
##    # set settings to the Scons Arguments list... is this needed????
##    SCons.Script.ARGUMENTS.update(common.g_args)
##        
   
    

# used to help scripts set defaults when there is no config script

def SetOptionDefault(key,value):
    import sys
    def_env=SCons.Script.DefaultEnvironment()
    rpt=def_env['PARTS_REPORTER']
    args = sys.argv[1:]
    if common.g_part_mode=='help':
        return
    global def_args

    rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
    common.g_defaultoverides[key]=value
    
    
    
    
##    if (key=='config' or key=='mode') and common.is_string(value) and not common.is_list(value):
##        value=string.split(value,',')
##    elif key=='tool_chain' and common.is_string(value) and not common.is_list(value):
##        value=common.process_tool_arg(string.split(value,','))
##    
##    try:
##        #get data so we can figure out type ( to handle correctly later)
##        val=common.g_args[key]
##        #get Def value
##        def_val=common.def_args.get(key,None)
##        
##        #Based on type try to do correct logic
##        if common.is_string(val):
##            if val=='':
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##            elif val==def_val and def_val != None:
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##            
##        elif common.is_list(val):
##            if val==[]:
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##            elif val==def_val and def_val != None:
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##
##        elif common.is_bool(val):
##            l=len(key)
##            set=True
##            for a in args:
##                if a[:l] == key:
##                    set=False
##            if set==True:
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##        elif type(val) is type({}):
##            if val=={}:
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##            elif val==def_val and def_val != None:
##                rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##                common.g_args[key]=value
##            
##            
##    except KeyError:
##        rpt.part_message('Setting default value of '+str(key)+' to ' +str(value))
##        common.g_args[key]=value


            
def opt_target(option, opt, value, parser):
        import SCons.Script.Main
        lst=string.split(value, '-')
        if len(lst) > 2:
            raise OptionValueError("Warning:  %s is not a valid --target_platform value\nValue must be in form of <Plaform>-<Architecture>" % o)
        if len(lst) == 1:
            # nice to a have short cut
            tmp=platform_info.MapArchitecture(lst[0])
            if tmp == '':
                #assume this was a platform
                parser.values.target_platform=platform_info.SystemPlatform(
                    lst[0],platform_info._host_sys.ARCH
                    )
            else:
                #assume this is a architure
                parser.values.target_platform=platform_info.SystemPlatform(
                        platform_info._host_sys.OS,lst[0]
                        )
        else:
            p=lst[0]
            a=lst[1]
            if p == '':
                p=platform_info._host_sys.OS
            if a == '':
                a=platform_info._host_sys.Architecture
            parser.values.target_platform=platform_info.SystemPlatform(p,a)


SCons.Script.AddOption("--cfg_file",
            dest='cfg_file',
            default='parts.cfg',
            nargs=1, type='string',
            action='store',
            help='Configuration file used to store common settings')
            
SCons.Script.AddOption("--verbose",
            dest='verbose',
            default=None,
            nargs=1, type='string',
            action='store',
            help='Control the level of detail information printed')
                 
##            
##SCons.Script.AddOption("--tool_chain",
##            dest='tool_chain',
##            default=[],#'default',
##            nargs=1,
##            callback=opt_chain,
##            type='string',
##            action='callback',
##            help='Tool chains to use for build')
            
SCons.Script.AddOption("--target","--target_platform",
            dest='target_platform',
            default=platform_info.SystemPlatform(platform_info._host_sys.OS,platform_info._host_sys.ARCH),#'default',
            nargs=1,
            callback=opt_target,
            type='string',
            action='callback',
            help='Sets the default TARGET_PLATFORM use for cross builds')
        

# add configuartion varaible needed for basic setup
#common.add_config_var('cfg_file','parts.cfg')



def tool_converter(str_val, raw_val):
    if common.is_string(raw_val):
        tmp=raw_val.split(',')
        lst=[]
        for i in tmp:
            lst.append(i.split('_'))
        return lst
    if common.is_list(raw_val):
        return raw_val
    raise "Invalid tool value '%s'" % RawVal
    
common.AddVariable('tool_chain',['default'],'The tool chain to use by default',converter=tool_converter)   

common.AddVariable('show_progress',True,'Controls is progress state is shown')
common.AddVariable('PROGRESS_STR',['scons: Evaluating |\r',
                                    'scons: Evaluating /\r',
                                    'scons: Evaluating -\r',
                                    'scons: Evaluating \\\r'],#'scons: Evaluating $TARGET\r')
                                    'What is used to show progress state')

#common.add_config_var('use_sdk_for','')

common.AddVariable('use_source_for','','Controls what Part and dependents to build from source when building off of SDKs')
common.AddBoolVariable('use_sdk',False, 'Controls if SDKs dependents are used to build target instead of sources')

#common.AddVariable('cfg_file','parts.cfg')
