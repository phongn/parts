import os
import time
import SCons.Script 
import core
import common
import vcs
import part_logger
import packaging
import copy

# these imports add stuff we will need to export to the parts file.
import platform_info 

import version
import node_helpers
import functors
import sdk
import reporter
from pattern import Pattern


##'''
##'cpgl2_test': { 'ALIAS': 'cpgl2_test',
##                'CCFLAGS': [],
##                'CFLAGS': [],
##                'CPPDEFINES': ["${PARTID('cpgl','2.*','CPPDEFINES',True)}"],
##                'CPPPATH': ["${PARTID('cpgl','2.*','CPPPATH',True)}"],
##                'CREATE_SDK': [ ( 'InstallItem',
##                                  [ '$INSTALL_BIN',
##                                    <parts.common._make_rel instance at 0x03D18DC8>,
##                                    '',
##                                    '',
##                                    False,
##                                    False]),
##                                ( 'InstallItem',
##                                  [ '$INSTALL_BIN',
##                                    <parts.common._make_rel instance at 0x03D1C6E8>,
##                                    '',
##                                    '',
##                                    False,
##                                    False])],
##                'CXXFLAGS': [],
##                'DEPENDSON': [ <<pieces>dependon.component instance at 0x03D0F8A0>],
##                'ENV': <SCons.Script.SConscript.SConsEnvironment instance at 0x037AA648>,
##                'EXPORTED_BINS': [],
##                'EXPORTED_HEADERS': [],
##                'EXPORTED_LIBS': [],
##                'FILE': <SCons.Node.FS.File instance at 0x03D0F940>,
##                'LIBPATH': ["${PARTID('cpgl','2.*','LIBPATH',True)}"],
##                'LIBS': ["${PARTID('cpgl','2.*','LIBS',True)}"],
##                'LINKFLAGS': [],
##                'MAKES_SDK': True,
##                'NAME': 'cpgl_test',
##                'PARENT_ALIAS': None,
##                'PARENT_NAME': None,
##                'ROOT_ALIAS': 'cpgl2_test',
##                'ROOT_NAME': "${PARTNAME('cpgl2_test')}",
##                'SDK_FILE': <SCons.Node.FS.File instance at 0x03D138C8>,
##                'SHORT_ALIAS': 'cpgl2_test',
##                'SHORT_NAME': 'cpgl_test',
##                'SHORT_VERSION': '2.0',
##                'TARGET_FILES': [ <SCons.Node.FS.File instance at 0x03D15440>,
##                                  <SCons.Node.FS.File instance at 0x03D15648>,
##                                  <SCons.Node.FS.File instance at 0x03D181C0>,
##                                  <SCons.Node.FS.Entry instance at 0x03D18B70>,
##                                  <SCons.Node.FS.File instance at 0x03D1C440>,
##                                  <SCons.Node.FS.Entry instance at 0x03D1C760>,
##                                  <SCons.Node.FS.File instance at 0x03D138C8>,
##                                  <SCons.Node.FS.File instance at 0x03D13670>],
##                'VERSION': <parts.version.version instance at 0x03D139E0>},
##'''

g_parts={} # generally only root/topp level parts

class Part_t:
    def __init__(self,alias,parts_file,mode=[],vcs_type=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,
            **kw):

##        # set up state of aliases so we can make the correct key
##        def_env=SCons.Script.DefaultEnvironment()
##        parent_alias=def_env.get('DEFINING_PART',None)
##        
##        sdk_file=[None]
##        if parent_alias != None:
##            alias=parent_alias+'.'+alias
                        
        self.alias = alias
        
        self.file=parts_file # the Parts file to read in
        self.mode=mode # special mode value used by part file to configure itself
        self.vcs=vcs_type # how we can get the source, None is local
        self.set_as_default_target=default # do we set this as a default build target
        
        self.append=append
        self.prepend=prepend
        self.create_sdk=create_sdk
        self.package_groups=package_groups
        self.kw=kw        
        
        self.Processed=False
        
        g_parts.append(self)
        
    def Process(self):
        Part(**self.stuff)
        
    def store():
        pass
        

def jj(): #delete this.. using to collapse section in editor
    pass
##class Part_t:
##    def __init__(self,alias,parts_file,mode=[],vcs_type=None,default=False,
##                    append={},prepend={},create_sdk=True,parent_part=None,**kw):
##                    
##        self.vcs=vcs_type # how we can get the source, None is local
##        self.set_as_default_target=default # do we set this as a default build target
##        self.mode=mode # special mode value used by part file to configure itself
##        self.file=parts_file # the Parts file to read in
##        self.create_sdk=create_sdk
##        self.append=append
##        self.prepend=append
##        self.parent=parent_part
##        self.kw=kw        
##        g_parts.append(self)
##        
##        # other core setup
##           
##        # the path and location to the sub .scons file
##        ## The Alias...
##
##        # setup which part is being defined.
##        # we hold old state as needed. We create the name based on the
##        # currently defined Part + .<new part name>
##        if parent_alias!=None:
##            # existing part is being define, this subpart is defines as
##            # parentpart.subpart
##            self.alias=parent_alias+'.'+short_alias 
##        else:
##            self.alias=short_alias
##
####        #setup state ####needed?
####        def_env['DEFINING_PART']=alias
####    
####        # Part Alias
####        env['ALIAS']=self.alias
####        env['PART_ALIAS']=self.alias
##        # The Alias Parent
##        self.parent_alias=parent_alias
##        # The Alias Short Form
##        self.short_alias=alias
##
##        # some data we will use for our own DB file
##        if common.g_name_alias_map.has_key(alias) == False:
##            common.g_name_alias_map[alias]=set()
##            
##        #setup the root info
##        #root_info=part_info
##        #while root_info['PARENT_ALIAS'] != None:
##            #root_info=def_env['PART_INFO'][root_info['PARENT_ALIAS']]
##            #common.g_name_alias_map[alias].add(root_info['ALIAS'])
##
##        #the Alias Root
##        self.root_alias=root_info['ALIAS']    
##
##        ## FILE STUFF
##        if self.parts_file != None:
##            # force subst to make sure funny path issues are handled
##            self.parts_file=env.subst(self.parts_file)
##    
##            # do any checkout/copy/updates needed
##            # update the parts_file location
##            self.parts_file=vcs.process_vcs(env,vcs_type,parts_file)
##
##            # work around in Scons bug
##            if self.parts_file[1] == ':' or self.parts_file[0]=='/':
##                self.parts_file=env.File(self.parts_file)
##            else:
##                curr_path=env.Dir('.').srcnode().abspath
##                slef.parts_file=env.File(os.path.join(curr_path,self.parts_file))
##                #parts_file=env.Dir('.').srcnode().File(parts_file)
##        
##        #part_info['FILE']=parts_file
##    
##        ## The names..
##        #the short name
##        self.short_name=None
##        #the Root name
##        self.root_name="${PARTNAME('"+self.root_alias+"')}"
##    
##        if parent_alias==None:
##            #The full name
##            self.name=None
##            #the Parent name
##            self.parent_name=None
##        
##            # some default version info
##            self.version=version.version('0.0.0')
##            self.short_version='0.0'
##        else:
##            #The full name
##            self.name="${PARTNAME('"+parent_alias+"')}.${PARTSHORTNAME('"+part_info['ALIAS']+"')}"
##            #the Parent name
##            self.parent_name="${PARTNAME('"+parent_alias+"')}"
##            
##            # some default version info
##            self.version="${PARTS('"+root_info['ALIAS']+"','VERSION')}"
##            self.short_version="${PARTS('"+root_info['ALIAS']+"','SHORT_VERSION')}"
##
##        #refernece to this env .. for better resolution later
##        #part_info['ENV']=env
##    
##        #list of what we dependon 
##        self.dependson=[]
##    
##        # some stuff for the SDK .. need to clean up latter
##        self.exported_headers=[]
##        self.EXPORTED_LIBS=[]
##        self.EXPORTED_BINS=[]
##
##        #all the file that are outputted by a builder inside the part
##        self.target_files=[]
##    
##        #def_env[name]=part_info
##        #if def_env.has_key('PART_INFO')==False:
##            #def_env['PART_INFO']={}
##        #if def_env['PART_INFO'].has_key(alias):
##            #rpt.part_warning(env,'Overriding predefined alias ['+alias+'] file=['+str(def_env['PART_INFO'][alias]['FILE'])+'] with data from part file=['+str(part_info['FILE'])+']')
##        #print 'Parts: Warning= Overriding predefined alias [',alias,'] file=[',def_env['PART_INFO'][alias]['FILE'],'] with data from part file=[',part_info['FILE'],']'
##    
##        
##        
##        
##    
##    def generate(self,env):
##        
##    def has_vcs(self):
##        return self.vcs is not None
##        
##    def vcs(self)
##        return self.vcs
##    
##    def installed_files(self,type=None):
##        ret=filter(,self.installed_files)
##        return self.installed_files
##        
##    def exported_items(self):
##        #returns list of item type exported, such as headers, flags
##        
##    def exported_item(self,type):
##        
##
##        
        

def make_part_info(env,parts_file,short_alias,parent_alias,vcs_type=None):
    def_env=SCons.Script.DefaultEnvironment()
    
    part_info={}
    
    # we assume all parts make SDK.. else they will modify this value latter
    part_info['MAKES_SDK']=True
    
    
    # the path and location to the sub .scons file
    ## The Alias...

    # setup which part is being defined.
    # we hold old state as needed. We create the name based on the
    # currently defined Part + .<new part name>
    if parent_alias!=None:
        # existing part is being define, this subpart is defines as
        # parentpart.subpart
        alias=parent_alias+'.'+short_alias 
    else:
        alias=env.subst(env.get('ALIAS_PREFIX','')+short_alias+env.get('ALIAS_POSTFIX',''))
        

    #setup state
    def_env['DEFINING_PART']=alias
    
    # Part Alias
    part_info['ALIAS']=alias
    env['ALIAS']=alias
    env['PART_ALIAS']=alias
    # The Alias Parent
    part_info['PARENT_ALIAS']=parent_alias
    # The Alias Short Form
    part_info['SHORT_ALIAS']=short_alias
    env['SHORT_ALIAS']=short_alias
    # some data we will use for our own DB file
    if common.g_name_alias_map.has_key(alias) == False:
        common.g_name_alias_map[alias]=set()
            
    #setup the root info
    root_info=part_info
    while root_info['PARENT_ALIAS'] != None:
        root_info=def_env['PART_INFO'][root_info['PARENT_ALIAS']]
        common.g_name_alias_map[alias].add(root_info['ALIAS'])

    #the Alias Root
    part_info['ROOT_ALIAS']=root_info['ALIAS']    

    ## FILE STUFF
    if parts_file != None:
        # force subst to make sure funny path issues are handled
        parts_file=env.subst(parts_file)
    
        # do any checkout/copy/updates needed
        # update the parts_file location
        parts_file=vcs.process_vcs(env,vcs_type,parts_file)
        part_info['VCS_OBJECT']=vcs_type

        # work around in Scons bug
        if parts_file[1] == ':' or parts_file[0]=='/':
            parts_file=env.File(parts_file)
        else:
            curr_path=env.Dir('.').srcnode().abspath
            parts_file=env.File(os.path.join(curr_path,parts_file))
            #parts_file=env.Dir('.').srcnode().File(parts_file)
        
    part_info['FILE']=parts_file
    
    ## The names..
    #the short name
    part_info['SHORT_NAME']=None
    #the Root name
    part_info['ROOT_NAME']="${PARTNAME('"+root_info['ALIAS']+"')}"
    
    if parent_alias==None:
        #The full name
        part_info['NAME']=None
        #the Parent name
        part_info['PARENT_NAME']=None
        
        # some default version info
        part_info['VERSION']=version.version('0.0.0')
        part_info['SHORT_VERSION']='0.0'
    else:
        #The full name
        part_info['NAME']="${PARTNAME('"+parent_alias+"')}.${PARTSHORTNAME('"+part_info['ALIAS']+"')}"
        #the Parent name
        part_info['PARENT_NAME']="${PARTNAME('"+parent_alias+"')}"
            
        # some default version info
        part_info['VERSION']="${PARTS('"+root_info['ALIAS']+"','VERSION')}"
        part_info['SHORT_VERSION']="${PARTS('"+root_info['ALIAS']+"','SHORT_VERSION')}"

    #refernece to this env .. for better resolution later
    part_info['ENV']=env
    
    #list of what we dependon 
    part_info['DEPENDSON']=[]
    
    # some stuff for the SDK .. need to clean up latter
    part_info['EXPORTED_HEADERS']=[]
    part_info['EXPORTED_LIBS']=[]
    part_info['EXPORTED_BINS']=[]

    #all the file that are outputted by a builder inside the part
    part_info['TARGET_FILES']=[]
    part_info['INSTALLED_FILES']=[]
    
    # not sure if i will need this or not ...
    part_info['SUB_PARTS']=[]
    
    #def_env[name]=part_info
    if def_env.has_key('PART_INFO')==False:
        def_env['PART_INFO']={}
    if def_env['PART_INFO'].has_key(alias):
        reporter.report_warning('Overriding predefined alias ['+alias+'] file=['+str(def_env['PART_INFO'][alias]['FILE'])+'] with data from part file=['+str(part_info['FILE'])+']')
        
    
    return part_info
    

def Part_method(env1,alias,parts_file,mode=[],vcs_type=None,default=False,
                append={},prepend={},create_sdk=True,package_group=None,**kw):
    
    new_kw={}
    new_append={}
    new_prepend={}
    new_kw.update(env1.get('PARTS_KW',{}))
    new_append.update(env1.get('PARTS_APPEND',{}))
    new_prepend.update(env1.get('PARTS_PREPEND',{}))
    package_group=env1.get('PARTS_PACKAGE_GROUPS',package_group)
    if mode==[]:
        mode=env1['MODE']
    new_kw.update(kw)
    new_append.update(append)
    new_prepend.update(prepend)
    Part(alias,parts_file,mode,vcs_type,default,new_append,new_prepend,
    create_sdk,package_group,**new_kw)
    tmp=env1.get('PART_INFO',None)
    if tmp is not None:
        tmp['SUB_PARTS'].append(env1['PART_ALIAS']+'.'+alias)
    
def Part(alias,parts_file,mode=[],vcs_type=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,
            **kw):
    reporter.SetPartStackFrameInfo()
    start_time=time.time()
    #print "defining" ,alias
    if common.g_part_mode=='help':
        return


    def_env=SCons.Script.DefaultEnvironment()
    
    parent_alias=def_env.get('DEFINING_PART',None)
    
    sdk_file=[None]
    if parent_alias == None:
        talias=alias#def_env.subst(kw.get('ALIAS_PREFIX',def_env.get('ALIAS_PREFIX',''))+
                     #           alias+
                      #          kw.get('ALIAS_POSTFIX',def_env.get('ALIAS_POSTFIX','')))
        # empty list to save mem if this is a root part
        sdk.g_sdked_files=set([])
        # this allows us to decide if we want to continue processing this file or not
        # if not we will return. The second part of this is to see if we modify the part file
        # we will read to be the original, or the generated one.
        sdk_file=core.process_part(talias)
    else:
        
        talias=parent_alias+'.'+alias

    if sdk_file == None:
        #print "Skipping",talias
        #print talias,'\t\t',time.time() - start_time,"seconds"
        return    
    ## process the part
    part_info={}
    
    ## setup the basics
    # Get the enviroment to use
    env=core.generate_config(prepend.copy(),append.copy(),kw.copy())
    
    ## logger and task spawners
    spawn=env['PART_SPAWNER']
    env['PART_LOG_MAPPER']=part_logger.part_logger(env,reporter.g_rpter.console)
    env['SPAWN']=spawn(env)
    
    # add to our set of Env with builders
    #common.g_env_w_builders.add(id(env))

    if kw != {}:
        env['PARTS_KW']=kw
    if append != {}:
        env['PARTS_APPEND']=append
    if prepend != {}:
        env['PARTS_PREPEND']=prepend
    # get our current ABS path for later use
    curr_path=env.Dir('.').srcnode().abspath
    ## Setup the global state 
    
    ## store part specfic data
    base_str=None
    if sdk_file != [None]:
        base_str=env.subst('Building from SDK -- ${PART_ALIAS_CONCEPT}')
        part_info=make_part_info(env,sdk_file,alias,parent_alias,None)
    else:
        if parent_alias == None:
            base_str=env.subst('Building from source -- ${PART_ALIAS_CONCEPT}')
        
        part_info=make_part_info(env,parts_file,alias,parent_alias,vcs_type)
    if base_str:
        reporter.print_msg(env.subst(base_str+part_info['ALIAS']))
    alias=part_info['ALIAS']
    parts_file=part_info['FILE']

    def_env['PART_INFO'][alias]=part_info

    #helps with debugging
    env['PART_INFO']=part_info
    
    ## package logic ( as it is currently)
    if package_group:
        packaging.PackageGroup(package_group,alias)
    part_info['PACKAGE_GROUPS']=package_group
    env['PARTS_PACKAGE_GROUPS']=package_group

    ## Setup the enviroment with dependent libs, include, etc...
    libpath=['$BUILD_DIR']
    env.Append(LIBPATH=libpath)
    
    ## add information on how to map this Parts
    # allow us to make a part platform indepent in some way
    # Might want to change this to be a enum like setup
    part_info['PLATFORM_MATCH']=copy.copy(env['TARGET_PLATFORM'])
    if kw.get('platform_independent',kw.get('platform_indepenent',False)):
        part_info['PLATFORM_MATCH']=platform_info.SystemPlatform('any','any')
    if kw.get('os_independent',kw.get('os_indepenent',False)):
        part_info['PLATFORM_MATCH'].OS='any'
    if kw.get('architecture_independent',kw.get('architecture_indepenent',False)):
        part_info['PLATFORM_MATCH'].ARCH='any'
    

    # test to what we want to the SRC_DIR to be.. works around
    # annoying behavior of Root Sconstruct file not working with
    # with other files not under it directory tree
    s=os.path.split(part_info['FILE'].srcnode().abspath)[0]
    if s=='':
        s=curr_path
    env['SRC_DIR']=env['PART_DIR']=s
    
    if mode == []:
        mode=env['mode']
    #env['mode']=common.make_list(kw.get('mode',[]))
    env['MODE']=common.make_list(mode)
    
    ##alias info
    env['PART_ROOT_ALIAS']=part_info['ROOT_ALIAS']
    env['PART_PARENT_ALIAS']=part_info['PARENT_ALIAS']
    
    ## name info
    env['PART_NAME']="${PARTNAME('"+alias+"')}"
    env['PART_SHORT_NAME']="${PARTSHORTNAME('"+alias+"')}"    
    env['PART_ROOT_NAME']="${PARTS('"+alias+"','ROOT_NAME')}"
    env['PART_PARENT_NAME']="${PARTS('"+alias+"','PARENT_NAME')}"

    ## version info
    env['PART_VERSION']="${PARTS('"+alias+"','VERSION')}"
    env['PART_SHORT_VERSION']="${PARTS('"+alias+"','SHORT_VERSION')}"
    
    ## file info
    env['PART_FILE']=parts_file
    
    ##  some backward compatible stuff to later remove
    ## also we ahve some stuff for mapping the export var correctly while
    ## handling some ugly wrapper to ceratina object i would rather have as 
    ## pieces
    export_map=common.g_parts_objs
    
    AbsFile=node_helpers._AbsFile(env)
    AbsDir=node_helpers._AbsDir(env)
    
    export_map['AbsFile']=AbsFile
    export_map['AbsDir']=AbsDir
    export_map['env']=env
    
    # this should force Scons to be called and warn if the file does not
    # exist, except when we are cleaning and the checked out version
    # does not exists
    ret=None
    if (common.g_part_mode=='build') or (os.path.exists(parts_file.srcnode().abspath)==True):
        if os.path.exists(parts_file.srcnode().abspath)==False:
            reporter.report_warning('Parts file '+parts_file.srcnode().abspath+" was not found. The build may fail")
            
        # Call the part file        
        if env['CONTINUE_ON_EXCEPTION']:
            try:
                reporter.ResetPartStackFrameInfo()
                ret=def_env.SConscript(
                    parts_file,
                    src_dir=env.subst('$SRC_DIR'),
                    variant_dir=env.subst('$BUILD_DIR'),
                    duplicate=env['duplicate_build'],
                    exports=export_map
                    )
            except Exception,ec:
                import traceback,StringIO
                ec_str=StringIO.StringIO()
                traceback.print_exc(file=ec_str)
                reporter.report_warning("Exception thrown while processing "+parts_file.srcnode().abspath+"\n"+ec_str.getvalue())
                reporter.print_msg("Will try to continue...")
                #env.Exit(1)
        else:
            reporter.ResetPartStackFrameInfo()
            ret=def_env.SConscript(
                    parts_file,
                    src_dir=env.subst('$SRC_DIR'),
                    variant_dir=env.subst('$BUILD_DIR'),
                    duplicate=env['duplicate_build'],
                    exports=export_map
                    )

    reporter.SetPartStackFrameInfo()
    ## Setup SDK stuff
 
    if (env['CREATE_SDK'] == False and create_sdk == True):
        create_sdk=False;
    
    pinfo=def_env['PART_INFO'][alias]
    if create_sdk==True:
        #set up the builder for the SDK file
        v=env.__CreateSDKBuilder__([],parts_file)
        part_info['SDK_FILE']=v[0]
        # needs to depend on all the file existing in the SDK 
        # else the builder may fail.
        env.Requires(v,env.Alias('_${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+alias))
        env.Alias('${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+alias,v)
        if pinfo.has_key('CREATE_SDK') == False:
                pinfo['CREATE_SDK']=[]
        if parent_alias!=None:
            parent_pinfo=def_env['PART_INFO'][parent_alias]
            if parent_pinfo.has_key('CREATE_SDK') == False:
                parent_pinfo['CREATE_SDK']=[]
            sdkname=pinfo['NAME']+'_'+pinfo['VERSION']+'.sdk.parts'
            args={'alias':pinfo['SHORT_NAME'],'parts_file':sdkname,
            'mode':mode,
            'vcs_type':None,'default':default,'append':append,'prepend':prepend,
            'create_sdk':False}
            parent_pinfo['CREATE_SDK'].append(('Part',[common.named_parms(args),
            common.named_parms(kw)])) 
    

    ## here we map the alias tree

    # this builder allows us to map what parts tries to map... 
    # nice for debugging build issues and making depends mapping graphs
    # need better mapping.. for now we map to abstract 'package'
    vfile=env._MapUnknowns([],parts_file)
    env.Alias("version_mapping::",vfile)
    env.Alias("package",vfile)       
        
    #build alias
    build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
    # this aliasmap below is modifed to make sure parts that call stuff like
    # make under the hood or any other action that prevents build directory
    # from being made, from stopping desired behavior
    a=env.Alias("_"+build_alias)
    a2=env.Alias(build_alias,[a,env.Dir(env.subst('$BUILD_DIR'))])
    env.Clean(a,env.subst('$BUILD_DIR'))
    common.g_name_alias_map[alias].add("_"+build_alias)
    common.g_name_alias_map[alias].add(build_alias)
    common.make_alias_tree(env,'${PART_BUILD_CONCEPT}',a2)

    #sdk alias stuff
    sdk_alias='${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
    a=env.Alias(sdk_alias,[a])
    common.g_name_alias_map[alias].add(sdk_alias)
    common.make_alias_tree(env,'${PART_SDK_CONCEPT}',a)
    
    #install alias stuff
    install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
    a=env.Alias(install_alias,[a])
    common.g_name_alias_map[alias].add(install_alias)
    common.make_alias_tree(env,'${PART_INSTALL_CONCEPT}',a)
    
    #add to queue the delayed mapping of any dependent stuff
    def_env['PREPROCESS_LOGIC_QUEUE'].append(functors.map_parts_alias(env))
    
    
    #main alias
    a=env.Alias(alias,[a])
    common.g_name_alias_map[alias].add(alias)
    
    a=env.Alias('${PART_ALIAS_CONCEPT}'+alias,a)
    common.g_name_alias_map[alias].add(env.subst('${PART_ALIAS_CONCEPT}')+alias)
    # all alias??
    env.Alias('${PART_ALIAS_CONCEPT}',a)
    pv_alias=common.make_alias_tree(env,'${PART_NAME_CONCEPT}',a)
    
    env.Alias('all',[pv_alias])
    
    # basic clean stuff .. note this might clean stuff in a way that 
    # scons should have clean in other ways but failed to.. 
    # may cause a false postive bug to be filed
    ## NOte the all cases we might want to move to a new location
    #ta=env.Alias(env.subst(part_info['ROOT_ALIAS']))
##    if common.def_args['OUT_INCLUDE'] == env['OUT_INCLUDE']:
##        #print alias,env.Dir('$OUT_INCLUDE')
##        env.Clean(ta,env.Dir('$OUT_INCLUDE'))
##    if common.def_args['OUT_LIB'] == env['OUT_LIB']:
##        #print env.Dir('$OUT_LIB').srcnode().abspath
##        env.Clean(ta,env.Dir('$OUT_LIB'))
##    if common.def_args['OUT_BIN'] == env['OUT_BIN']:
##        #print env.Dir('$OUT_BIN').srcnode().abspath
##        env.Clean(env.Alias('all'),env.Dir('$OUT_BIN'))
##    if common.def_args['BUILD_DIR'] == env['BUILD_DIR']:
##        #print "build",env.Dir('$BUILD_DIR').abspath
##        env.Clean(ta,env.Dir('$BUILD_DIR').abspath)
##    if common.def_args['OUT_BIN_ROOT'] == env['OUT_BIN_ROOT']:
##        #print env.Dir('$OUT_BIN').srcnode().abspath
##        env.Clean(env.Alias('all'),env.Dir('$OUT_BIN_ROOT'))
##    if common.def_args['OUT_LIB_ROOT'] == env['OUT_LIB_ROOT']:
##        #print env.Dir('$OUT_BIN').srcnode().abspath
##        env.Clean(env.Alias('all'),env.Dir('$OUT_LIB_ROOT'))
##    if common.def_args['OUT_INCLUDE_ROOT'] == env['OUT_INCLUDE_ROOT']:
##        #print env.Dir('$OUT_BIN').srcnode().abspath
##        env.Clean(env.Alias('all'),env.Dir('$OUT_INCLUDE_ROOT'))
##    if common.def_args['BUILD_DIR_ROOT'] == env['BUILD_DIR_ROOT']:
##        #print env.Dir('$OUT_BIN').srcnode().abspath
##        env.Clean(env.Alias('all'),env.Dir('$BUILD_DIR_ROOT'))

    #double check that the Part name mapping has been defined
    # if the user did not call PartName() then this would not be setup
    if def_env.has_key('PART_IDS')==False:
        def_env['PART_IDS']={}
    # See that the ID Alias list exists
    name=env.PartName()
    if name not in def_env['PART_IDS']:
        def_env['PART_IDS'][name]=[]
        # Append to the ID list with new alias
        def_env['PART_IDS'][name].append(alias)
        pinfo['NAME']=name

    # must be last statement for this function
    if default==True:
        def_env.Default(pv_alias)
    
    def_env['DEFINING_PART']=parent_alias   
    #print alias,'\t\t',time.time() - start_time,"seconds"
    reporter.ResetPartStackFrameInfo()
    


    
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.Part=Part_method

# add configuartion varaible needed for part
common.AddVariable('PART_BUILD_CONCEPT','build${ALIAS_SEPARTATOR}','Namespace used to just build a a given target')

common.AddVariable('ALIAS_POSTFIX','','')
common.AddVariable('ALIAS_PREFIX','','')

common.AddVariable('PART_ALIAS_CONCEPT','alias${ALIAS_SEPARTATOR}','Namespace to express building via an Alias target')
common.AddVariable('PART_NAME_CONCEPT','name${ALIAS_SEPARTATOR}','Namespace to express building via a Part Name and possible version')
common.AddVariable('BUILD_DIR_ROOT','#build', 'Root directory for building a given build configuration/variant')
common.AddVariable('BUILD_DIR','$BUILD_DIR_ROOT/${CONFIG}_${TARGET_PLATFORM}/$ALIAS', 'Full path used to for building a given build configuration/variant')


common.add_global_value('Part',Part)
common.add_global_value('part',Part)