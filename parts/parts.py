import os
import time
import SCons.Script 
import core
import common
import part_logger
import packaging
import copy
import dependson
import requirement
from target_type import target_type

# these imports add stuff we will need to export to the parts file.
import platform_info 

import version
import node_helpers
import functors
import reporter
from pattern import Pattern

import pprint

g_known_names={}

class Part_t(object):
    def __init__(self,file,mode=[],vcs_t=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,alias=None,name=None,
            **kw):
   
        ## stuff for creating an environment 
        # need to store this so we can pass to an sub-part
        self.__append=append #This is stuff we want to append to the environment
        self.__prepend=prepend # this is stuff we would want to prepend
        self.__kw=kw # this is stuff we want to replace        
        self.__mode=common.make_list(mode)
        #version number.. ideally this maps to root version only
        # but in some cases we need it in Parts that are not fully defined yet
        self.__version=version.version(kw.get('version','0.0.0'))
        ## sdk stuff
        # do we want to create the sdk or skip it
        self.__create_sdk=create_sdk
        # This is the data for the SDK file we will want to make
        self.__create_sdk_data=[] 
        # the file that are copied in to the SDK
        self.__sdk_files=[] 
        # the name of the SDK file we will make.. if any
        self.__sdk_file=None 
        
        ##packaging stuff
        # what package group to add this to
        self.__package_group=package_group
        
        ## state stuff
        self.__set_as_default_target=default # do we set this as a default build target
        
        # the part has been fully processed or not
        self.__Processed=False
        # the file has been read
        self.__is_read=kw.get('__is_read',False)
        # this is the style/format the part file used
        self.__format=None
        
        # everything we dependon, implict and explict, 
        # contain component objects.. change to part and component mix latter??
        self.__full_dependson=[] 
        self.__dependson=[] # has to be a list as the order matters for linking
        # these are Parts that this Part uses, but may not depend on.
        # we will make sure these are processed before this Part is processed
        # used primarly for classic formats
        # otherwise the Depends on logic will try to verify these object for possible
        # matches, else error. ie IF the part name matches the rest of it has to
        # dependons staements with no matching name fall trhought the "global"
        # set of Parts to match
        # ideally stored only on root_parts
        if self.__kw.get('parent_part',None) is None:
            self.__uses=common.make_list(kw.get("requires",[]))
        
        # data we will cache later
        self.__cache={}
        # the sections we can define in a part
        self.__sections={}
        # the environment object for the Part
        self.__env=None 
        self.__env_exports={}
        
        ##basic data
        # the alias.. such as 
        self.__alias=alias
        self.__short_alias=alias
        #The part name.. parent.name+.+short_name
        self.__name=name
        # the short name.. or exact value given to this part as the name
        self.__short_name=name
        # the parent part object
        self.__parent=None
        # the top level part object
        self.__root=None
        # any subparts to this Part
        self.__sub_parts={}
        
        ## collection of data we make during the build
        
        # this is the data we need to have export to other components            
        self.__exports={} 
        
        # data the we build.. don't need order only that it happens
        self.__part_nodes=set() # any node that belongs to this part to build or check for
        self.__target_files=set() # any $TARGET that is built are part of this component
        self.__installed_files=[] # the file that are installed for this Part
        # files that effect the possible good state of this build context 
        # of anything this Part might fix
        self.__build_context_files=set() 
        self.__config_context={}
        # all the aliases that map to this part object
        # such as install::name like stuff or utest::name_version
        self.__alias_set=set() 

        # how we can get the source, None is local
        self.__vcs=vcs_t 
        # the file for this part, if any
        self.__file=file
        # the src_path we need to make sure SCons as no issues when loading the Part file
        self.__src_path=None
        # this is how we can depend on this object
        self.__platform_match=None
        self.__is_setup=False
        
        # use to help with ordering in a compatible way between classic and new formats
        self.__order_value=0
        
        # this is to help with issues with unit tests sub parts in classic format
        self.__sdk_or_installed_called=False
        
        # this to force loading .. bypassing caching features
        self.__force_load=kw.get('force_load',False)

    # see if we can remove the env arg latter
    def _setup_(self,_env=None):
        
        ss=time.time()
        # is this core like the iapat object?
        if _env is None:
            self.__env=core.generate_config(
                        self.__prepend.copy(),
                        self.__append.copy(),
                        self.__kw.copy()
                    )
        else:
            self.__env=_env
        #print "env time",time.time()-ss
        # new way to get env???
        #self.env=runtime_context.Environment()
        
        
        #basic data
        
        
        ##we need to check if this is a sub Parts 
        # check for kw for parent_part key
        self.__parent=self.__kw.get('parent_part',None)         
        global g_known_names
        #We need to set to the alias value as this is the unique ID used to map data internally
        if self.__parent is None:
            # this is the parent so we apply the global Prefix add Postfix values
            if self.__alias is None:
                
                # we don't have a user provided alias.. make it off the file name
                tmp=self.__env.subst(self.__file)
                tmp=os.path.splitext(os.path.split(tmp)[1])[0] # we only want the file name
                # see if we have seen this file name before 
                if tmp in g_known_names:
                    tmp="%s%s"%(tmp,g_known_names[tmp]+1)
                    g_known_names[tmp]+=1
                else:
                    tmp="%s"%(tmp)
                    g_known_names[tmp]=0
                self.__alias=tmp
                self.__short_alias=tmp
            self.__alias=self.__env.subst('${ALIAS_PREFIX}%s${ALIAS_POSTFIX}'%self.__short_alias)
            
            self.__root=self
            self.__version=version.version('0.0.0')
        else:            
            #we have a parent
            #We need to set to the alias value as this is the unique ID used to map data internally
            if self.__alias is None:
                
                # we don't have a user provided alias.. make it off the file name
                tmp=self.__env.subst(self.__file)
                tmp=os.path.split(tmp)[1] # we only want the file name
                self.__alias=tmp
                self.__short_alias=tmp
            
            self.__alias=self.__parent.Alias+'.'+self.__short_alias
            #self.__name=self.__parent.Name+'.'+self.__short_name
            self.__root=self.__parent.Root
            self.__parent._add_sub_parts(self)
            
            
            
        
        ## resolve the File name for the Part we will load latter
        self.__make_part_env()
        if self.__parent is None:
            dir_tmp=self.__env.Dir('#')
        else:
            dir_tmp=self.__env.Dir(self.__parent.__src_path)
        if self.__vcs is None:
            # we have no vcs object.. so we take file name as is
            self.__file=dir_tmp.File(self.__env.subst(self.__file)) # the Parts file to read in
        else:
            # we have a vcs object.. ask vcs object for resolved file name
            self.__vcs._setup_(self) # update env with vcs level defines
            self.__file=dir_tmp.File(self.__vcs.PartFileName)
        
        # the src_path we need to make sure SCons as no issues when loading the Part file
        self.__src_path=os.path.split(self.__file.srcnode().abspath)[0]        
        
        ## file info
        self.__env['PART_FILE']=self.__file
        self.__env['SRC_DIR']=self.__env['PART_DIR']=self.__src_path
        
        ## add information on how to map this Parts
        ## allow us to make a part platform independent in some way
        self.__platform_match=copy.copy(self.__env['TARGET_PLATFORM'])
        if self.__kw.get('platform_independent ',self.__kw.get('platform_indepenent',False)):
            self.__platform_match=platform_info.SystemPlatform('any','any')
        if self.__kw.get('os_independent ',self.__kw.get('os_indepenent',False)):
            self.__platform_match.OS='any'
        if self.__kw.get('architecture_independent ',self.__kw.get('architecture_indepenent',False)):
            self.__platform_match.ARCH='any'
        self.__is_setup=True
        
    
    def _update(self,alias=None,name=None,Version=None,file=None,mode=[],vcs_t=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,
            **kw):
        '''
        The logic here is to only add value here until the component is setup
        Once it is setup we don't want any value to overide existing values. 
        This mean the Part from the user point of view is read-only.
        .. need to refactor more ...
        '''
        if self.__is_setup == False:
            self.__alias=alias
            self.__name=name
            self.__version=version.version(Version)
            self.__file=file
            self.__mode=common.make_list(mode)
            self.__vcs=vcs_t
            self.__set_as_default_target=default
            self.__append=append
            self.__prepend=prepend
            self.__create_sdk=create_sdk
            self.__kw=kw
            self.__package_group=package_group
        elif alias==None and name==None and version==None and file==None\
            and file==None and mode==[] and vcs_type==None and default==False\
            and append=={} and prepend == {} and create_sdk==True and package_group==None:
            pass
        else:
            reporter.report_error('Part alias = "%s" already has been setup.'%(self.__alias))
    
    def _merge(self,otherobj):
        #turn other object in to this guy the best we can
        otherobj.__dict__=self.__dict__    
    
    # accessors that are more for Parts developer
    def _set_version(self,version):
        if self._is_root:
            self.__version = version
        else:
            self.__root._set_version(version)
            
    def _set_name(self,name,force_parent=None):
        if force_parent is not None:
            self.__name=force_parent+'.'+name
        elif self.__parent is not None:
            self.__name=self.__parent.Name+'.'+name
        elif self.__parent is None:
            self.__name=name
        self.__short_name=name
        common.g_engine._part_manager.add_name_alias(self.__name,self.__alias)
            
    def _add_build_context_files(self,lst):
        ''' 
        Add files that define part of this components build_context
        '''
        
        if self._is_root:
            self.__build_context_files.update(lst)
        else:
            self.__root._add_build_context_files(lst)
    
    def _add_config_context_files(self,lst):
        ''' 
        Add information needed for seeing in the configuration files are different
        In this case we want to store the tool, and the file that was loaded for
        that tool, if there was any
        '''
        if self._is_root:
            self.__config_context.update(lst)
        else:
            self.__root._add_config_context_files(lst)
            
    def _uses_part(self,obj):
        ''' return True if the part passed in is used by this parts'''
        if self._is_root:
            # need to test that this works as expected
            return obj in self._uses
        return self.__root._uses_part(obj)
    
    def _add_sub_parts(self,obj):
        if self.__sub_parts.has_key(obj.Alias):
            reporter.report_error("%s is already defined"%obj.Alias)
        self.__sub_parts[obj.Alias]=obj
                    
    @property
    def _uses(self):
        if self._is_root:
            try:
                return self.__cache['uses']
            except KeyError:
                tmp=[]
                for p in self.__uses:
                    if common.is_string(p):
                        # assume this is an Alias
                        tmp_alias=p
                        p=common.g_engine._part_manager._from_alias(p)
                        if p is None:
                            reporter.report_error('Cannot use non existing Part "%s"'%tmp_alias)
                    elif isinstance(p,Part_t):
                        #just a Validation check
                        pass
                    else:
                        reporter.report_error('Inavlid type for a Part to dependon "%s"'%(type(p)))
                    tmp.append(p)
                self.__cache['uses']=tmp
            return self.__cache['uses']
        else:
            return self.__root._uses

    @property
    def _force_load(self):
        return self.__force_load
                    
    @property
    def _file(self):
        return self.__file
    
    @property
    def _sdk_file(self):
        return self.__sdk_file
    
    @property
    def _sdk_files(self):
        return self.__sdk_files
        
    @property
    def _target_files(self):
        return self.__target_files
    
    @property
    def _part_nodes(self):
        return self.__part_nodes
    
    @property
    def _part_nodes(self):
        return self.__part_nodes
    
    @property
    def _installed_files(self):
        return self.__installed_files
    
    @property
    def _exports(self):
        return self.__exports
    
    @property
    def _env_exports(self):
        '''This is for backward compatiblity??'''
        return self.__env_exports
    
    @property
    def _cache(self):
        return self.__cache
    
    @property
    def _platform_match(self):
        return self.__platform_match

    @property
    def _kw(self):
        return self.__kw

    @property
    def _append(self):
        return self.__append

    @property
    def _prepend(self):
        return self.__prepend

    @property
    def _package_group(self):
        return self.__package_group     
    
    @property
    def _create_sdk_data(self):
        return self.__create_sdk_data

    @property
    def _mode(self):
        return self.__mode
    
    def _set_order_value(self,x):
        self.__order_value=x
    
    @property
    def _order_value(self):
        return self.__order_value
    
      
    def _set_depends(self,val):
        """Get the return all(indirect and direct) Parts that this part depends on."""
        common.extend_if_absent(self.__dependson,val)
        
    def _set_full_depends(self,val):
        """Get the return all(indirect and direct) Parts that this part depends on."""
        self.__full_dependson=val
        
    def _set_part_format(self,s):
        '''
            currently set to new or classic.. need to clean up latter to something better
        '''
        self.__format=s
        
        
    def _get_part_format(self):
        return self.__format
    
    @property
    def _is_classic_format(self):
        return self.__format=='classic' or self.__format is None
    
    @property
    def _is_root(self):
        return self.__alias == self.__root.Alias
    
    @property
    def _is_read(self):
        return self.__is_read
        
    # some properties ( public use)
    
    @property
    def Alias(self):
        """Get the current alias."""
        return self.__alias
    
    @property
    def ShortAlias(self):
        """Get the current alias."""
        return self.__short_alias
    
    @property
    def alias(self):
        """for backwards compatibility."""
        return self.__alias
    
    @property
    def Version(self):
        """Get the current version."""
        if self._is_root:
            return self.__version
        return self.__root.Version
    
    @property
    def ShortVersion(self):
        """Get the current short version."""
        return self.__root.__version[0:2]

    @property
    def Name(self):
        """Get the current parent Part name."""
        if self.__name is None:
            return self.__alias
        return self.__name

    @property
    def ShortName(self):
        """Get the current parent Part name."""
        if self.__short_name is None:
            return self.__short_alias
        return self.__short_name    
    
    @property
    def ParentName(self):
        """Get the current parent Part name."""
        if self.__parent is None:
            return None
        return self.__parent.Name

    @property
    def RootName(self):
        """Get the current root Part name."""
        return self.__root.Name

    @property
    def SourcePath(self):
        """Get the current parent Part source path."""
        return self.__src_path
    
    def _source_path(self,path):
        """Get the current parent Part source path."""
        self.__env['SRC_DIR']=self.__env['PART_DIR']=self.__src_path=path
        return self.__src_path

    @property
    def Depends(self):
        """Get the local/direct Parts this part depends on."""
        return self.__dependson

    @property
    def FullDepends(self):
        """Get the return all(indirect and direct) Parts that this part depends on."""
        return self.__full_dependson
    
    @property
    def Env(self):
        """get the default environment used with this Part"""
        return self.__env
    
    @property
    def Root(self):
        """Get the current root Part."""
        return self.__root

    @property
    def Parent(self):
        """Get the current parent Part."""
        return self.__parent
    
    @property
    def Vcs(self):
        """Get the current parent Part."""
        if self.__vcs:
            return self.__vcs
        import vcs.null
        return vcs.null.null
    
    @property
    def _sdk_or_installed_called(self):
        return self.__sdk_or_installed_called
        
    @_sdk_or_installed_called.setter
    def _sdk_or_installed_called(self,value):
        self.__sdk_or_installed_called=value
    
    def __make_part_env(self):
        
        # set alias
        
        self.__env['ALIAS']=self.__alias
        self.__env['PART_ALIAS']=self.__alias
        # The Alias Parent
        #part_info['PARENT_ALIAS']=parent_alias
        
        # The Alias Short Form
        self.__env['SHORT_ALIAS']=self.__short_alias
        
        ## logger and task spawners
        spawn=self.__env['PART_SPAWNER']
        self.__env['PART_LOG_MAPPER']=part_logger.part_logger(self.__env,reporter.g_rpter.console)
        self.__env['SPAWN']=spawn(self.__env)
        
        
        ## package logic ( as it is currently)
        self.__env['PARTS_PACKAGE_GROUPS']=self.__package_group
        if self.__package_group is not None: 
            packaging.PackageGroup(self.__package_group,self.__alias)
        

        ## Setup the enviroment BUILD_DIR in the LIBPATH
        # might need more.. to add as needed
        libpath=['$BUILD_DIR']
        self.__env.Append(LIBPATH=libpath)
        
        # setup the mode
        self.__mode.extend(self.__env['mode'])
        self.__env['MODE']=self.__mode
        
        ##alias info
        self.__env['PART_ROOT_ALIAS']=self.__root.Alias
        if self.__parent:
            self.__env['PART_PARENT_ALIAS']=self.__parent.Alias
        else:
            self.__env['PART_PARENT_ALIAS']=None
        
        ## name info
        self.__env['PART_NAME']="${PARTNAME('"+self.__alias+"')}"
        self.__env['PART_SHORT_NAME']="${PARTSHORTNAME('"+self.__alias+"')}"    
        self.__env['PART_ROOT_NAME']="${PARTS('"+self.__root.__alias+"','Name')}"
        if self.__parent is None:
            self.__env['PART_PARENT_NAME']=None
        else:
            self.__env['PART_PARENT_NAME']="${PARTS('"+self.__parent.__alias+"','Name')}"

        ## version info
        self.__env['PART_VERSION']="${PARTS('"+self.__alias+"','Version')}"
        self.__env['PART_SHORT_VERSION']="${PARTS('"+self.__alias+"','ShortVersion')}"
        
    
##        # some data we will use for our own DB file
##        if common.g_name_alias_map.has_key(alias) == False:
##            common.g_name_alias_map[alias]=set()
            
    
    def __str__(self):
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(self.__dict__)

        
    def _map_alias(self):
        ''' This function maps two different of Core Aliases
        One form is to map the given component to all components that it dependson
        The second form is to add all sub-Parts of this component
        '''
        
        vfile=self.__env._MapUnknowns([],self.__file)
        
        ##given part alias of "foo" name "FOO"
        #build alias .. ie build::alias::foo
        #build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias
        # this aliasmap below is modifed to make sure parts that call stuff like
        # make under the hood or any other action that prevents build directory
        # from being made, from stopping desired behavior
        #a=self.__env.Alias("_"+build_alias,vfile) # _build::foo
        #build::foo->_build::alias::foo 
        #          ->Dir($SRC_DIR)
        #a2=self.__env.Alias(build_alias,[a,self.__env.Dir(self.__env.subst('$SRC_DIR'))])
        # forces all of the build directory to clean
        #self.__env.Clean(a,self.__env.subst('$BUILD_DIR'))
        # store values for latter.. rethink??
        #self._add_alias("_"+build_alias)
        #self._add_alias(build_alias)
        # make and map tree in case of subparts
        # this is stuff like: given build::FOO.sub1.sub2
        # we make a map like:
        # build::FOO->build::FOO.sub1->build::FOO.sub1.sub2
        #common.make_alias_tree(self.__env,'${PART_BUILD_CONCEPT}',a2)

        #sdk alias stuff
        #sdk::alias::foo
        #sdk_alias='${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias
        #sdk::alias::foo->_build::foo
        #a=self.__env.Alias(sdk_alias,[a])
        #self._add_alias(sdk_alias)
        # make and map tree in case of subparts
        # this is stuff like: given sdk:FOO.sub1.sub2
        # we make a map like:
        # sdk::foo->sdk::FOO.sub1->sdk::FOO.sub1.sub2->_build::alias::foo.sub1.sub2
        #common.make_alias_tree(self.__env,'${PART_SDK_CONCEPT}',a)
    
        #install alias stuff.. install::alias::foo
        #install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias
        #a=self.__env.Alias(install_alias,[a])
        #self._add_alias(install_alias)
        # make and map tree in case of subparts
        # this is stuff like: given sdk:foo.sub1.sub2
        # we make a map like:
        # install::FOO->install::FOO.sub1->install::FOO.sub1.sub2->sdk::alias::foo.sub1.sub2
        #common.make_alias_tree(self.__env,'${PART_INSTALL_CONCEPT}',a)
    
        #main alias
        #foo->install::alias::foo
        #a=self.__env.Alias(self.__alias,[a])
        #self._add_alias(self.__alias)
        #alias::foo->foo
        #a=self.__env.Alias('${PART_ALIAS_CONCEPT}'+self.__alias,a)
        #self._add_alias(self.__env.subst('${PART_ALIAS_CONCEPT}')+self.__alias)
        #alias::->alias::foo
        #self.__env.Alias('${PART_ALIAS_CONCEPT}',a)
        #name::<partname>->alias::foo
        #pv_alias=common.make_alias_tree(self.__env,'${PART_NAME_CONCEPT}',a)
        #all->name::foo
        #self.__env.Alias('all',[pv_alias])
        
        # This is the base Alias for a given Part
        build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias
        # note that InstallXXX and SdkXXX map to this value
        # new formats will make all targets to this value as well.
        a=self.__env.Alias(build_alias,vfile)
        self.__env.Alias("${PART_BUILD_CONCEPT}",a)
        #if self._is_root:
            #self.__env.Alias("${PART_BUILD_CONCEPT}",a)
        #else:
            #self.__env.Alias("${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}"+self.Parent.Alias,a)
        
        
        #add to queue the delayed mapping of high level Alias to other high level alias
        def_env=SCons.Script.DefaultEnvironment()
        common.g_engine.add_preprocess_logic_queue(functors.map_parts_alias(self.__env))
        # add call back for latter full mapping of build context
        common.g_engine.add_preprocess_logic_queue(functors.map_build_context(self))

    def _setup_sdk(self):
        create_sdk=True
        if (self.__env['CREATE_SDK'] == False and self.__create_sdk == True):
            create_sdk=False;
        
        if create_sdk==True:
            #set up the builder for the SDK file
            v=self.__env.__CreateSDKBuilder__([],self.__file)
            self.__sdk_file=v[0]
            #self.__env.Alias('${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias,v)
            self.__env.Alias('${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias,v)
            
            if self.__parent!=None:
                sdkname="%s_%s.sdk.parts"%(self.__name,self.Version)
                args={'alias':self.__short_alias,'parts_file':sdkname,
                'mode':self.__mode,
                'vcs_type':None,'default':self.__set_as_default_target,'append':self.__append,'prepend':self.__prepend,
                'create_sdk':False}
                self.__parent._create_sdk_data.append(('Part',[common.named_parms(args),
                common.named_parms(self.__kw)])) 

    def _map_targets(self):
        ''' 
        Here we map all known target files that happen in this component 
        to the alias value, to ensure that it is built in case there are actions
        that are no mapped correctly to some action that is mapped to the alias
        such as and sdk or install action
        '''
        
        # seems to be an issue for compatibility
        
        utest_call=False
        targets=SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp=target_type(t)
            sep_len=len(self.__env.subst("$ALIAS_SEPARTATOR"))
            if tmp.concept == self.__env.subst('$BUILD_UTEST_CONCEPT')[:-sep_len] or tmp.concept == self.__env.subst('$RUN_UTEST_CONCEPT')[:-sep_len]:
                utest_call=True
                break
        # if we are not building unit tests
        # and this is a classic format
        # and this part did not call any SdkXXX or InstallXXX
        # then we don't want to define any build actions it may have
        if utest_call==False and self._sdk_or_installed_called==False and self._is_classic_format:
            pass
        else:
            for i in self.__target_files:
              self.__env.Alias('${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias,i)
        # we also add them to known nodes at this time
        self.__part_nodes.update(self.__target_files)
        

    def IsProcessed(self):
        return self.__Processed == True
        
    def ReadFile(self):
        # we process the file
        # and check at the end if we processed a new format or an old format
        # error on mixed formats??
        
        if self.__is_read:
            print "\033[1;32m %swas already read"%self.__alias

        if self.__is_read==False:
            # final set up for environment
            self.__is_read=None
            #common.g_part_being_processed.append(self.__alias)
            #self.UpdateOnDisk()
            
            ## setup what we want to export
            # global objects
            export_map=common.g_parts_objs
            #global object that need to be mapped
            for k,v in common.g_parts_objs_env.items():
                export_map[k]=v(self.__env)
            # add the sections
            # we do this when we read as there might have been new sections dynamically added
            for s in common.g_sections:
                self.__sections[s.name]=s.Type()(self.__env)
            export_map.update(self.__sections)
            
            # add the environment
            export_map['env']=self.__env
            self.__env._log_keys=True
            # sort of ugly.. but SCon was to aggressive here in storing state
            try:
                del self.__file._memo['stat']
            except KeyError:
                pass
            bdir=self.__env.Dir(self.__env.subst('$BUILD_DIR'))
            
            sdir=self.__env.Dir(self.__src_path)
            if (common.g_engine._build_mode=='build') or (os.path.exists(self.__file.srcnode().abspath)==True):
                if os.path.exists(self.__file.srcnode().abspath)==False:
                    reporter.report_error('Parts file '+self.__file.srcnode().abspath+" was not found.")
                
                # Call the part file        
                if self.__env['CONTINUE_ON_EXCEPTION']:
                    # don't error is the Parts file has bad data
                    # we just report it and go on
                    # will mostly fail if one needs to build everything
                    # however if i was to build on a component this 
                    # probally will allow me to continue without waiting for the 
                    # one bad component to get fixes
                    try:
                        reporter.ResetPartStackFrameInfo()
                        ret=self.__env.SConscript(
                            self.__file,
                            src_dir=self.__env.subst('$SRC_DIR'),
                            variant_dir=self.__env.subst('$BUILD_DIR'),
                            duplicate=self.__env['duplicate_build'],
                            exports=export_map
                            )
                    except Exception,ec:
                        import traceback,StringIO
                        ec_str=StringIO.StringIO()
                        traceback.print_exc(file=ec_str)
                        reporter.report_warning("Exception thrown while processing "+self.__file.srcnode().abspath+"\n"+ec_str.getvalue())
                        reporter.print_msg("Will try to continue...")
                        
                else:
                    
                    reporter.ResetPartStackFrameInfo()
                    
                    ret=self.__env.SConscript(
                            self.__file,
                            src_dir=sdir,
                            variant_dir=bdir,
                            duplicate=self.__env['duplicate_build'],
                            exports=export_map
                            )
            #print bdir
            #print "*",bdir.srcnode()
            
            # we tag the Directory nodes so we can latter sort unknown items faster, by checking the directory ownership
            #pp=pprint.PrettyPrinter()
            #pp.pprint(bdir.__dict__)
            self.__env._log_keys=False
            common.tag_node_ownership(self.__env,bdir)
            
            # set file as read
            self.__is_read=True
            

    def _hasTargetFiles(self):
        return self.__target_files != set([])

    def _add_alias(self,name):
        self.__alias_set.add(self.__env.subst(name))

    
    ## sections API's
    def _has_section_defined(self,name):
        ''' 
        tests to see if a certain section is defined
        return None if the file has not been read (ie this is unknown)
        otherwise it returns True or False
        '''
        if self.__is_read:
            return name in self.__sections
        return None
    
    def _has_valid_sections(self):
        '''
        This will function will do two things
        1) reduce the map of sections to only those that have data
        2) return true or false if any sections are good
        Error reporting! If we have bad sections we throw an expections
        '''
        # reduce
        for name,obj in self.__sections.items():
            # see if the section was even called
            if obj.isSet():
                # if so is it valid() in that non optional phases 
                # have been called
                if not obj.isValid():
                #We have an error
                    reporter.report_error("Section %s did not define all required phases!\n Define phases are:%s\n Required Phases are:%s"%
                    [name,obj.FoundPhases(),RequiredPhases()])
            else:
                #we don't have anything in the section as it was not called
                # in this case remove it
                del self.__sections[name]
        return self.__sections != {}
    
    def _has_section_phase_been_called(self,section,phase):
        '''
        Tells us if this section and phase has been called already
        Returns True or False
        
        This allow the processfunc of a section to see if it needs to call this
        section phase or not to prevent wasted time in processing known items
        '''
        try:
            if self.__cache["%s%scalled"%(section,phase)]:
                return True
        except KeyError:
            return False
        
    def _call_section(self,section,phase):
        '''
        Call the section function defined for a given phase.
        This will cache the fact that it was called, so it get called only once
        It will throw an error if there is no such combination defined
        '''
        try:
            if self.__cache["%s%scalled"%(section,phase)]:
                return
        except KeyError:
            tmp=self.__env.fs.getcwd()
            try:
                self.__env.fs.chdir(self.__env.Dir(self.__env.subst("$BUILD_DIR")),True)
            except OSError:
                self.__env.fs.chdir(self.__env.Dir(self.__env.subst("$BUILD_DIR")))
                os.chdir(self.__env.Dir(self.__env.subst("$BUILD_DIR")).srcnode().abspath)
            
            lst=getattr(self.__sections[section],'func_'+phase)
            if lst ==[]:
                reporter.report_warning("No phase function callbacks for %s.%s in Part %s"%(section,phase,self.__name))
            for i in lst:
                i(self.__env)

            self.__env.fs.chdir(tmp,True)
            self.__cache["%s%scalled"%(section,phase)]=True


    
    # some depend on stuff
    def map_component_info(self,comp_part):
    
        cpppath=[]
        libpath=[]
        libs=[]
        cppdefines=[]
        linkflags=[]
        ccflags=[]
        cflags=[]
        cxxflags=[]
        
        # map stuff we dependon
        if (comp_part.requires & requirement.REQ._CPPPATH_IMPORT):
            cpppath=common.extend_unique(cpppath,comp_part.part._exports.get('CPPPATH',''))
        if (comp_part.requires & requirement.REQ._LIBPATH_IMPORT):
            libpath=common.extend_unique(libpath,comp_part.part._exports.get('LIBPATH',''))
        if (comp_part.requires & requirement.REQ._LIBS_IMPORT):
            libs=common.extend_unique(libs,comp_part.part._exports.get('LIBS',''))
        if (comp_part.requires & requirement.REQ._LINKFLAGS_IMPORT):
            linkflags=common.extend_unique(linkflags,comp_part.part._exports.get('LINKFLAGS',''))
        if (comp_part.requires & requirement.REQ._CCFLAGS_IMPORT):
            ccflags=common.extend_unique(ccflags,comp_part.part._exports.get('CCFLAGS',''))
        if (comp_part.requires & requirement.REQ._CFLAGS_IMPORT):
            cflags=common.extend_unique(cflags,comp_part.part._exports.get('CFLAGS',''))
        if (comp_part.requires & requirement.REQ._CXXFLAGS_IMPORT):
            cxxflags=common.extend_unique(cxxflags,comp_part.part._exports.get('CXXFLAGS',''))
        if (comp_part.requires & requirement.REQ._CPPDEFINES_IMPORT):
            cppdefines=common.extend_unique(cppdefines,comp_part.part._exports.get('CPPDEFINES',''))

        #common.append_if_absent( self.__dependson,comp_part)
        #add the dependent info

        self.__env.Append(
            CPPPATH=cpppath,LIBPATH=libpath,LIBS=libs,CPPDEFINES=cppdefines,
            LINKFLAGS=linkflags,CCFLAGS=ccflags,CFLAGS=cflags,CXXFLAGS=cxxflags
            )
    #    reporter.verbose_msg("Duplicate",env.subst($CPPDEFINES))            
        cpppath=[]
        libpath=[]
        libs=[]
        cppdefines=[]
        libflags=[]
        ccflags=[]
        cflags=[]
        cxxflags=[]
        
        # map what we need to export
        if (comp_part.requires & requirement.REQ._CPPPATH_EXPORT):
            cpppath=common.extend_unique(cpppath,comp_part.part._exports.get('CPPPATH',''))
            if 'CPPPATH' not in self.__exports:
                self.__exports['CPPPATH']=[]
            self.__exports['CPPPATH']=common.extend_unique(self.__exports['CPPPATH'],cpppath)
        if (comp_part.requires & requirement.REQ._LIBPATH_EXPORT):
            libpath=common.extend_unique(libpath,comp_part.part._exports.get('LIBPATH',''))
            if 'LIBPATH' not in self.__exports:
                self.__exports['LIBPATH']=[]
            self.__exports['LIBPATH']=common.extend_unique(self.__exports['LIBPATH'],libpath)
        if (comp_part.requires & requirement.REQ._LIBS_EXPORT):
            libs=common.extend_unique(libs,comp_part.part._exports.get('LIBS',''))
            if 'LIBS' not in self.__exports:
                self.__exports['LIBS']=[]
            self.__exports['LIBS']=common.extend_unique(self.__exports['LIBS'],libs)
        if (comp_part.requires & requirement.REQ._LINKFLAGS_EXPORT):
            linkflags=common.extend_unique(linkflags,comp_part.part._exports.get('LINKFLAGS',''))
            if 'LINKFLAGS' not in self.__exports:
                self.__exports['LINKFLAGS']=[]
            self.__exports['LINKFLAGS']=common.extend_unique(self.__exports['LINKFLAGS'],linkflags)
        if (comp_part.requires & requirement.REQ._CCFLAGS_EXPORT):
            ccflags=common.extend_unique(ccflags,comp_part.part._exports.get('CCFLAGS',''))
            if 'CCFLAGS' not in self.__exports:
                self.__exports['CCFLAGS']=[]
            self.__exports['CCFLAGS']=common.extend_unique(self.__exports['CCFLAGS'],ccflags)
        if (comp_part.requires & requirement.REQ._CFLAGS_EXPORT):
            cflags=common.extend_unique(cflags,comp_part.part._exports.get('CFLAGS',''))
            if 'CFLAGS' not in self.__exports:
                self.__exports['CFLAGS']=[]
            self.__exports['CFLAGS']=common.extend_unique(self.__exports['CFLAGS'],cflags)
        if (comp_part.requires & requirement.REQ._CXXFLAGS_EXPORT):
            cxxflags=common.extend_unique(cxxflags,comp_part.part._exports.get('CXXFLAGS',''))
            if 'CXXFLAGS' not in self.__exports:
                self.__exports['CXXFLAGS']=[]
            self.__exports['CXXFLAGS']=common.extend_unique(self.__exports['CXXFLAGS'],cxxflags)
        if (comp_part.requires & requirement.REQ._CPPDEFINES_EXPORT):
            cppdefines=common.extend_unique(cppdefines,comp_part.part._exports.get('CPPDEFINES',''))
            if 'CPPDEFINES' not in self.__exports:
                self.__exports['CPPDEFINES']=[]
            self.__exports['CPPDEFINES']=common.extend_unique(self.__exports['CPPDEFINES'],cppdefines)
            
        #map up rpath with this.. ( need to fix up the Mac)
        #if self.env['HOST_PLATFORM']!='win32' and self.env['HOST_PLATFORM'] != 'darwin':
            
            #map_rpath_part(part,comp_part)
            #map_rpath_link_part(part,comp_part)

    def _full_parts_depends_list(self):
        ''' 
        make a full depends list ( internal and non internal) 
        '''
        
        if self.__full_dependson == []:
            dlst=self.__dependson
            flst=[]
            for d in dlst: 
                if d.part is None:
                    print "can't map",d.name,d.version
                    continue               
                flst.append(d.part.Alias)
                tmp=d.part._full_parts_depends_list()
                common.extend_unique(flst,tmp)
                self.__full_dependson=flst
        
        return self.__full_dependson

    def _parts_root_depends_list(self):
        ''' 
        These are the Root Parts needed process this Part correctly
        The Part it depend on might need other Part, so this is not a
        full list of items
        '''
        
        if self._cache.get('root_depends') is None:
            dlst=self.__dependson
            flst=[self.__root.Alias]
            self.__cache['root_depends']=[]
            for d in dlst:
                if d.part is None:
                    print "can't map",d.name,d.version
                    continue    
                tmp=d.part._parts_root_depends_list()
                common.extend_if_absent(flst,tmp)
            
            # do again for each subpart
            for s in self.__sub_parts.values():
                tmp=s._parts_root_depends_list()
                common.extend_if_absent(flst,tmp)
                
            self.__cache['root_depends']=flst
        return self.__cache['root_depends']
    
    def _full_parts_root_depends_list(self):
        ''' 
        These are the Root Parts needed process this Part correctly
        This is the full list of all item needed by this Part 
        and any of the sub Parts and any of the Parts that are dependents
        '''

        if self.__root._cache.get('root_depends_full') is None:
            if self._is_root:
                dlst=self.__dependson
                flst=[self.__alias]
                self.__root._cache['root_depends_full']=[]
                for d in dlst:         
                    if d.part is None:
                        pass
                    elif d.part.Root.Alias != self.Alias:       
                        tmp=d.part.Root._full_parts_root_depends_list()
                        common.extend_if_absent(flst,tmp)
                    
                # do again for each subpart
                for s in self.__sub_parts.values():
                    # get the list of Root parts this sub part needs
                    tmp=s._parts_root_depends_list()
                    # add it to the list
                    # note that we need to get the full list for each of these 
                    # items.. since there are good chance of duplicates
                    # we delay to go over this list once latter 
                    common.extend_if_absent(flst,tmp)
                    
                
                # now we go over the list to make sure all items are here
                # we do it here as doing it above could be more expensive with 
                # parts that have lots of sub parts
                for d in flst:         
                    if d != self.__root.Alias:       
                        tmp_pobj=common.g_engine._part_manager._from_alias(d)
                        tmp=tmp_pobj.Root._full_parts_root_depends_list()
                        common.extend_if_absent(flst,tmp)
                
                    
                self.__root._cache['root_depends_full']=flst
            else:
                return self.__root._full_parts_root_depends_list()
        
        return self.__root._cache['root_depends_full']        
        
    def _setup_from_cache_data(self,data):
        '''
        This will setup this part based on data in the cache
        The Part manager will call and create sub part as needed
        The part object should have been created and setup already for this call.
        This function should only have to setup stuff that this component would 
        have exported or outputed that needs to be shared with dependent components
        '''
        
        if self.__is_setup ==False:
            reporter.report_error("Part object setup from cache data requires part_t object to have been created and setup()")
        # map values that would normally be define in a "new" format
        # such as name and version
        self._set_name(data['short_name'])
        self._set_version(version.version(data['version']))
        #How to match this component in a dependon call by dependent components
        self.__platform_match=platform_info.SystemPlatform(data['platform_match'])
        
        ## might not need this one....
        # map what the part would depend on
        depends_list=[]
        for d in data['dependson']:
            depends_list.append(dependson.ComponentRef(**d))        
        self._set_depends(depends_list)
            
        #map exports of this component
        self.__exports=data['exports']
        # think this is for backward compatibility only at the moment
        # however might need to expand on this
        self.__env.Replace(**data['env_exports'])
        
        # need to add sdk file
        tmp=data.get('sdkfile',{}).get('name',None)
        self.__sdk_file=self.__env.File(tmp)
        
        # load some data that might be touched
        self.__full_dependson=data['full_depends']
        self.__cache['root_depends']=data['root_depends']
        if self._is_root:
            self.__cache['root_depends_full']=data['full_root_depends']
            
        
    def _get_cache_data(self):#store(self):
        reporter.verbose_msg(['parts_cache'],"Getting data for",self.__alias)
        
        data={}
        file={}
        # basic info
        data['name']=self.__name
        data['short_name']=self.__short_name
        data['alias']=self.__alias
        data['short_alias']=self.__short_alias
        data['version']=str(self.Version)
        # store all known sections that had been defined
        data['sections']=self.__sections.keys()
        # store all known aliases we made for the given part
        data['alias_set']=self.__alias_set
        # store the root_part
        data['root_alias']=self.__root.Alias
        # store the target_platform .. as this might be different from the default
        data['target_platform']=str(self.__env['TARGET_PLATFORM'])
        # store the target_platform .. as this might be different from the default
        data['config']=str(self.__env['CONFIG'])
        #the infomation on how this part should be matched via dependson
        data['platform_match']=str(self.__platform_match)
        #the packge group that this Parts is bound with
        data['package_group']=str(self.__package_group)
        #the mode that was passed to create this part
        data['mode']=self.__mode
        
        # here we store that context signiture for values passed in to the 
        
        #store any subparts
        tmp=[]
        for i in self.__sub_parts.values():
            tmp+=[i.Alias]
        data['subparts']=tmp
        #store parent info
        tmp=[]
        i=self.__parent
        while i is not None:
            tmp+=[i.Alias]
            i=i.Parent
        data['parents']=tmp
        #file info
        file={}
        if self.__file is None:
            file['name']=self.Parent._file.srcnode().path# check this
            file['csig']=self.Parent._file.get_csig()
            file['timestamp']=self.Parent._file.get_timestamp()
        else:
            file['name']=self.__file.srcnode().path# check this
            file['csig']=self.__file.get_csig()
            file['timestamp']=self.__file.get_timestamp()
        data['file']=file
        # we want to store the source path to help with part recreation from
        # cache data
        data['src_path']=self.__env.Dir(self.__src_path).path
        
        #direct sdk file data
        file={}
        if self.__sdk_file is None:
            file['name']=self.Parent._sdk_file.srcnode().path# check this
            file['csig']=self.Parent._sdk_file.get_csig()
            file['timestamp']=self.Parent._sdk_file.get_timestamp()
            
        else:
            file['name']=self.__sdk_file.srcnode().path# check this
            file['csig']=self.__sdk_file.get_csig()
            file['timestamp']=self.__sdk_file.get_timestamp()            
        data['sdkfile']=copy.copy(file)
        
        # store what we export
        # we expand the values here to reduce processing needs latter
        # the the reason we would store this is to speed up build latter
        for v in self.__exports.values():
            if common.is_list(v):
                for i in v:
                    if '$' in i:
                        self.__env.subst(i)
            else:
                if '$' in v:
                    self.__env.subst(v)
        data['exports']=self.__exports
        
        # this is for recreating a part from cache as these values are
        # set by the user and don't exist by default
        data['env_exports']=self.__env_exports
        # data about what this depends on we want the direct depend here
        # as this will allow us to speed up incremential build latter
        tmp=[]
        for d in self.__dependson:
            tmp.append({
                'name':d.name,
                'version_range':str(d.version),
                'requires':d.requires,
                'target_platform':str(d.target)
            })
        data['dependson']=tmp
        # data about what this depends on we want the full depend here
        data['full_depends']=self._full_parts_depends_list()
        # store all the root_parts we depend on
        data['root_depends']=self._parts_root_depends_list()
        # store all the root_parts we depend on
        data['full_root_depends']=self._full_parts_root_depends_list()
        ########
        ####### Below are node that we save!
        ####### skip for compatible behavior of 0.9 if utest or run_utest:: is not being used
        #######
        # figure out if utest was called
        utest_call=False
        targets=SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp=target_type(t)
            sep_len=len(self.__env.subst("$ALIAS_SEPARTATOR"))
            if tmp.concept == self.__env.subst('$BUILD_UTEST_CONCEPT')[:-sep_len] or tmp.concept == self.__env.subst('$RUN_UTEST_CONCEPT')[:-sep_len]:
                utest_call=True
                break
        # if we are not building unit tests
        # and this is a classic format
        # and this part did not call any SdkXXX or InstallXXX
        # then we don't want to define any build actions it may have
        if utest_call==False and self._sdk_or_installed_called==False and self._is_classic_format:
            data['nodes']=[]
            return data
        #store all known node that are mapped to this component as
        #a list of strings. we use the SCons DB to store the important data
        tmp=[]
        for i in self.__part_nodes:
            i.disambiguate()
            # see if node time stamp matches
            dbentry=i.get_stored_info()
            if i.has_builder()==False or getattr(dbentry,'ninfo',None) is None:
                # this should be some source node
                # or a node that should be ignored,
                # such as a "srcnode" version of a binary that would only exist
                # in the variant directory.. we test for the last case 
                # by testing for existance
                if i.exists(): # should test that this is not Value node
                    tmp.append(
                            {
                            'name':i.path,
                            'csig':i.get_csig(),
                            'timestamp':i.get_timestamp()
                            }
                        )
                #else:
                #    tmp.append(
                #            {
                #            'name':i.path,
                #            'csig':0,
                #            'timestamp':0
                #            }
                #        )
                    
            else:
                ninfo=dbentry.ninfo
                tmpd=i.path
                #tmpd={'name':i.path}
                #tmpd.update(ninfo.__dict__)
                tmp.append(tmpd)
            
        data['nodes']=tmp
        
        
        if self._is_root:
            # this is build context
            tmp=[]
            for i in self.__build_context_files:
                if i is None:
                    continue
                i=self.__env.File(i)
                # see if node time stamp matches            
                tmp.append(
                        {
                        'name':i.path,
                        'csig':i.get_csig(),
                        'timestamp':i.get_timestamp()
                        }
                    )
                        
            data['build_context']=tmp
            
            # this is config context ( like build but for the config files)
            tmp={}            
            for k,v in self.__config_context.items():            
                tmp[k]=[]
                for f in v:
                    i=self.__env.File(f)
                    # see if node time stamp matches            
                    tmp[k].append({
                            'name':i.abspath,
                            'csig':i.get_csig(),
                            'timestamp':i.get_timestamp()
                            })
                    
            data['config_context']=tmp
        return data


def Part_factory(arg1=None,parts_file=None,mode=[],vcs_type=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,
            alias=None,name=None,*lst,**kw):
    ''' This  function acts a factory to help with Part creation.
    This way control over making a new Part or getting the existing Part 
    can be better controled
    '''
    
    # handle common case:part(alias,file)
    if arg1 and parts_file is None:
        parts_file=arg1
    elif arg1 and parts_file and alias is None:
        alias=arg1
        
    Version=kw.get('version')
    tmp=None
    if alias or (name and Version):
        tmp=common.g_engine._part_manager._get_part(
            alias=alias,
            name=name,
            version=Version,
            target_platform=kw.get('TARGET_PLATFORM'))
        
    if tmp:

        if Version:
            del kw['version']
        #if name:
        #    del kw['name'] 
        tmp._update(alias,name,Version,
            parts_file,mode,vcs_type,default,
            append,prepend,create_sdk,package_group,
            **kw)
        if parts_file:
            tmp._setup_()
        return tmp
    
    tmp=Part_t(file=parts_file,mode=mode,vcs_t=vcs_type,
                    default=default,append=append,prepend=prepend,
                    create_sdk=create_sdk,package_group=package_group,
                    name=name,alias=alias,**kw)

    if parts_file:
        tmp._setup_()
    common.g_engine._part_manager._add_part(tmp)   
    
    return [tmp]

def SubPart_factory(env,arg1=None,parts_file=None,mode=[],vcs_type=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,alias=None,name=None,
            **kw):
            
    # handle common case:part(alias,file)
    if arg1 and parts_file is None:
        parts_file=arg1
    elif arg1 and parts_file and alias is None:
        alias=arg1
                
    return common.g_engine._part_manager._define_sub_part(
                        env,
                        alias,
                        parts_file,
                        mode,
                        vcs_type,
                        default,
                        append,
                        prepend,
                        create_sdk,
                        package_group,
                        **kw
                    )
                    

# This is what we want to be setup in parts



from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.Part=SubPart_factory

# add configuartion varaible needed for part
common.AddVariable('PART_BUILD_CONCEPT','build${ALIAS_SEPARTATOR}','Namespace used to just build a a given target')

common.AddVariable('ALIAS_POSTFIX','',' ')
common.AddVariable('ALIAS_PREFIX','','')

common.AddVariable('PART_ALIAS_CONCEPT','alias${ALIAS_SEPARTATOR}','Namespace to express building via an Alias target')
common.AddVariable('PART_NAME_CONCEPT','name${ALIAS_SEPARTATOR}','Namespace to express building via a Part Name and possible version')
common.AddVariable('BUILD_DIR_ROOT','#build', 'Root directory for building a given build configuration/variant')
common.AddVariable('BUILD_DIR','$BUILD_DIR_ROOT/${CONFIG}_${TARGET_PLATFORM}/$ALIAS', 'Full path used to for building a given build configuration/variant')


common.add_global_value('Part',Part_factory)
common.add_global_value('part',Part_factory)
