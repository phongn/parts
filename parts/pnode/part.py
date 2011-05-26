
from .. import glb

import pnode
import section
import part_info
import pnode_manager
from .. import api
from .. import common
from .. import settings
from .. import part_logger
from .. import packaging

#from .. import requirement
from .. import errors
from .. import functors
#from target_type import target_type
from .. import datacache

# these imports add stuff we will need to export to the parts file.
from .. import platform_info 
from .. import version
from .. import dependson
from .. import node_helpers

#from pattern import Pattern
import sys
import copy
import pprint
import os
import time
#import SCons.Script 
import SCons.Node
import types
import hashlib


class part(pnode.pnode):
    """description of class"""
    
    __slots__=[
    # calling params
    '__append',     # This is stuff we want to append to the environment
    '__prepend',    # this is stuff we would want to prepend
    '__kw',         # this is stuff we want to replace        
        
    # basic attibutes
    '__ID',
    '__file',         # the Parts file
    '__src_path',      # The Source path ( the path of the _file
    '__version',      # the version of this part
    '__name',         # the name of this part (foo.bar.goo)
    '__alias',        # the alias of this part (foo0.bar0.goo0)
    '__short_name',   # the short name of this parts (goo)
    '__short_alias',  # the short name of this parts (goo0)
    '__parent',       # the parent part object, else None
    '__root',         # the root part object, might be self
    '__subparts',      # dictionary of sub-parts 
    
    '__mode',          # special build values
    '__uses',      # list of Parts that this we want to map to first
    '__settings',       # The setting object used to create the enviornment
    '__env',            # the prime SCons Environment
    '__platform_match', # this is how we can depend on this object
    
    '__env_diff', # the difference of this environment with the Default environment of the defining Setting object
    '__env_diff_sig', # The MD5 value of this difference
    '__user_env_diff', # values that the user set in the Part file
    
    '__build_context_files', 
    '__config_context_files',
    
    '__sections', # the section the part contains
    '__classic_section', # the classic format case
    
    
    # sdk data 
    '__create_sdk',     # create the SDK
    '__create_sdk_data', # This is the data for the SDK file we will want to make
    '__sdk_files',      # the file that are copied in to the SDK
    '__sdk_file',       # the name of the SDK file we will make.. if any
    
    # some state stuff
    '__force_load', # tells us that this Parts should be loaded
    '__format',     #The format of the part file
    '__is_setup',    # the Parts has been setup to be buildable
    '__is_read',      # the file has been read
    '__is_default_target', # do we set this as a default build target
    '__defining_section', # current section we are defining
    '__read_state',
    
    #packaging stuff
    '__package_group', # the package group this maps to
    
    #VCS stuff
    '__vcs', #The information on how to check out this Part, None to use as file as local path.
    
    #compatiblity stuff
    '__sdk_or_installed_called', # this is to help with issues with unit tests sub parts in classic format
    '__order_value', # use to help with ordering in a compatible way between classic and new formats
    '__cache', # used for internal caching of data
    #'__dict__'
    ]
    # constructor
    def __init__(self,file=None,mode=[],vcs_t=None,default=False,
            append={},prepend={},create_sdk=True,package_group=None,alias=None,name=None,
            Settings=None,
            **kw):
        
        self.__ID=kw.get('ID')
        if self.__ID: del kw['ID']
        ## stuff for creating an environment 
        # need to store this so we can pass to an sub-part
        self.__append=append #This is stuff we want to append to the environment
        self.__prepend=prepend # this is stuff we would want to prepend
        self.__kw=kw # this is stuff we want to replace        
        self.__mode=common.make_list(mode)
        self.__settings=Settings
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
        self.__is_default_target=default # do we set this as a default build target
        
        # the part has been fully processed or not
        #self.__Processed=False
        # the file has been read
        self.__is_read=kw.get('__is_read',False)
        # this is the style/format the part file used
        self.__format=None
        
        # everything we dependon, implict and explict, 
        # contain component objects.. change to part and component mix latter??
#        self.__full_dependson=[] 
#        self.__dependson=[] # has to be a list as the order matters for linking
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
        self.__user_env_diff={}
        
        ##basic data
        # the alias.. such as 
        self.__alias=alias
        self.__short_alias=alias
        #The part name.. parent.name+.+short_name
        self.__name=name
        # the short name.. or exact value given to this part as the name
        self.__short_name=name
        # the parent part object
        # check for kw for parent_part key
        self.__parent=self.__kw.get('parent_part',None)
        if self.__parent:
            del self.__kw['parent_part']
        # the top level part object
        self.__root=None
        # any subparts to this Part
        self.__subparts={}
        
        
        self.__defining_section=None
        self.__classic_section=None
        
        ## collection of data we make during the build
        
        # files that effect the possible good state of this build context 
        # of anything this Part might fix
        self.__build_context_files=set() 
        self.__config_context_files={}
        
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
        
        # some state stuff
        try:
            self.__read_state=self.__read_state
        except:
            self.__read_state=glb.read_ignore
        

    
    @staticmethod
    def _process_arg(**kw):
        id = kw.get('ID')
        if id: setup= False
        else: setup = True
        return id,setup


    ## properties
    #calling params

    @property
    def _append(self):
        return self.__append

    @property
    def _prepend(self):
        return self.__prepend
    
    @property
    def _kw(self):
        return self.__kw

    # basic attributes
    @property #readonly non-mutable
    def File(self):
        return self.__file
    
    @property # readonly non-mutable
    def SourcePath(self):
        """Get the current parent Part source path."""
        return self.__src_path
    
    @SourcePath.setter
    def SourcePath(self,path):
        """Get the current parent Part source path."""
        self.__env['SRC_DIR']=self.__env['PART_DIR']=self.__src_path=path
        return self.__src_path
    
    @property
    def Version(self): # mutable
        """Get the current version."""
        if self.isRoot:
            return self.__version
        return self.__root.Version
    
    @Version.setter
    def Version(self,version):
        if self.isRoot:
            self.__version = version
        else:
            self.__root.Version=version
    
    @property # readonly as it based on full version
    def ShortVersion(self):
        """Get the current short version."""
        return self.__root.__version[0:2]
    
    @property #readonly non-mutable
    def Alias(self): 
        """Get the current alias."""
        return self.__alias
    
    @pnode.pnode.ID.getter
    def ID(self):
        if self.__ID is None:
            self.__ID=self.Alias
        return self.__ID
    
    @property #readonly non-mutable
    def ShortAlias(self):
        """Get the current alias."""
        return self.__short_alias
    
    @property #readonly non-mutable
    def alias(self):
        """for backwards compatibility."""
        return self.__alias
    
    @property
    def Name(self): #read only non-mutable as it based on short name and parent
        """Get the current parent Part name."""
        if self.__name is None:
            return self.__alias
        return self.__name
    
    @property # readonly 
    def ShortName(self):
        """Get the current parent Part name."""
        if self.__short_name is None:
            return self.__short_alias
        return self.__short_name    
    
    @ShortName.setter
    def ShortName(self, val):
        self._set_name(val)
    
    #For backward compatibility    
    def _set_name(self,name,force_parent=None):
        if force_parent is not None:
            self.__name=force_parent+'.'+name
        elif self.__parent is not None:
            self.__name=self.__parent.Name+'.'+name
        elif self.__parent is None:
            self.__name=name
        self.__short_name=name
        glb.engine._part_manager.add_name_alias(self.__name,self.__alias)
    
    @property #readonly mutable
    def Parent(self):
        """Get the current parent Part, or None if there is no parent"""
        return self.__parent

    @property #readonly mutable
    def Root(self):
        """Get the current root Part."""
        return self.__root

    @property #readonly non-mutabale #remove?
    def ParentName(self):
        """Get the current parent Part name."""
        if self.__parent is None:
            return None
        return self.__parent.Name

    @property #readonly non-mutabale #remove?
    def RootName(self):
        """Get the current root Part name."""
        return self.__root.Name

    @property #readonly non-mutable
    def SubParts(self):
        return self.__subparts.values()
    
    @SubParts.setter
    def SubParts(self,obj):
        try:
            if id(obj) != id(self.__subparts[obj.ID]):
                api.output.error_msg("%s is already defined"%obj.Alias)
        except KeyError:
            self.__subparts[obj.Alias]=obj
       
    @property
    def Mode(self): #readonly non-mutable
        return self.__mode # may want to return a copy
        
    @property #readonly non-mutabale
    def Uses(self):
        if self.isRoot:
            try:
                return self.__cache['uses']
            except KeyError:
                tmp=[]
                for p in self.__uses:
                    if common.is_string(p):
                        # assume this is an Alias
                        tmp_alias=p
                        p=glb.engine._part_manager._from_alias(p)
                        if p is None:
                            api.output.error_msg('Cannot use non existing Part "%s"'%tmp_alias)
                    elif isinstance(p,Part_t):
                        #just a Validation check
                        pass
                    else:
                        api.output.error_msg('Invalid type for a Part to dependon "%s"'%(type(p)))
                    tmp.append(p)
                self.__cache['uses']=tmp
            return self.__cache['uses']
        else:
            return self.__root.Uses
    
    def usesPart(self,obj):
        ''' return True if the part passed in is used by this parts'''
        if self.isRoot:
            # need to test that this works as expected
            return obj in self.Uses
        return self.__root.usesPart(obj)
        
    @property
    def Settings(self): #readonly mutable
        return self.__settings
        
    @property
    def Env(self):
        """get the default environment used with this Part"""
        return self.__env
    
    @property
    def PlatformMatch(self): #readonly 
        ''' Returns the SystemPlatform this part will match on for dependancies
        '''
        return self.__platform_match
    
    @property
    def _env_diff(self): #readonly
        return self.__env_diff
    
    @property
    def _env_diff_sig(self): #readonly
        return self.__env_diff
    
    @property
    def _user_env_diff(self):
        '''
        '''
        return self.__user_env_diff
    
    @property
    def _build_context_files(self):
        ''' 
        
        '''
        if self.isRoot:
            return self.__build_context_files
        else:
            return self.__root._build_context_files
    
    @property
    def _config_context_files(self):
        ''' 
        
        '''
        if self.isRoot:
            return self.__config_context_files
        else:
            return self.__root._config_context_files
    
    #sdk stuff (finish SDK stuff)
    @property
    def SdkFile(self):
        return self.__sdk_file
    
    @property
    def _sdk_files(self):
        return self.__sdk_files
    
    @property
    def _create_sdk_data(self):
        return self.__create_sdk_data
    
    @property
    def CreateSdk(self):
        return self.__create_sdk
    
    #State
    @property
    def ForceLoad(self):
        return self.__force_load
    
    @property
    def Format(self):
        return self.__format
    
    @Format.setter
    def Format(self,s):
        '''
        currently set to new or classic.. need to clean up latter to something better
        '''
        self.__format=s
        
    @property
    def isClassicFormat(self):
        return self.__format=='classic' or self.__format is None
    
    @property
    def isRoot(self):
        return self.__alias == self.__root.Alias
    
    @property
    def isSetup(self):
        '''returns if we have setup the environment for basic usage'''
        return self.__is_setup
    
    @property
    def isRead(self):
        '''Returns is we have read the file'''
        return self.__is_read
    
    @property
    def isDefaultTarget(self):
        '''Returns true is this Part is set as a default Target to be built'''
        return self.__is_default_target
    
    @property
    def isVisited(self):
        return self.isRead

    @isVisited.setter
    def _set_isVisited(self,value):
        pass
        
    #packaging stuff
    def PackageGroup(self):
        '''the Package group this Part is mapped to'''
        return self.__package_group
    
    #vcs stuff
    @property
    def Vcs(self):
        """return the VCS object"""
        if self.__vcs:
            return self.__vcs
        from ..vcs import null
        return null.null
    
    
    # some compatibility stuff
    @property
    def _sdk_or_installed_called(self):
        return self.__sdk_or_installed_called
        
    @_sdk_or_installed_called.setter
    def _sdk_or_installed_called(self,value):
        self.__sdk_or_installed_called=value
        
    @property
    def _order_value(self):
        return self.__order_value
    
    @_order_value.setter
    def _order_value(self,x):
        self.__order_value=x
    
    @property
    def _cache(self):
        return self.__cache
      

    # section forwarding API
    # given that we can only define one section at a time
    # may tweak when we get new formats working again
    @property
    def DefiningSection(self):
        if self.__defining_section:
            return self.__defining_section
        try:
            return self.__sections['build']
        except KeyError:
            pass
        return self.__classic_section
    
    @DefiningSection.setter
    def DefiningSection(self,sec):
        self.__defining_section=sec
    
    
    def Section(self,case):
        try:
            tmp=self.__sections[case]
            ## see if this needs to be loaded in
            ## should only happen if the section ( or this parts) is loaded in from stored info
            ## all other cases should be this full read in
            #if tmp.LoadState <pnode.readin:
            #    tmp.LoadFromCache()
            return tmp
        except:
            return self.__classic_section
    
    # hack till we get new format stuff working...
    def _AddSection(self,name,obj):
        self.__sections[name]=obj
        
    def SectionName(self):
        return None
        
    
    # re look at this function when we add new format 
    def _hasTargetFiles(self):
        return self.__classic_section.Targets != set([])


    # see if we can remove the env arg latter
    def _setup_(self,_env=None,*lst,**kw):
        # this value allows us a work around to the 
        # issue of generating an ID vs a full setup
        genid=kw.get('gen_ID')
        
        ss=time.time()
        # is this core like the iapat object?
        
        if _env is None:
            # if none have been setup, use the default Settings object
            if self.__settings==None:
                self.__settings=settings.DefaultSettings()
                
            self.__env=self.__settings.Environment(                
                        prepend=self.__prepend.copy(),
                        append=self.__append.copy(),
                        **self.__kw.copy()
                        )
            
        else:
            self.__env=_env
        
        
        ###basic data
        # create diff with default environment
        base_env=self.__settings.Environment()
        #check to see if the big three are different config, target_platform, toolchain
        #if so we want to diff off of that case, as these can item can make a mass set
        # of changes we really want to ignore, or don't care about as much as the
        # one item that caused them to change
        diff={}
        if self.__mode != []:
            diff={'mode':self.__mode}
        if base_env['TARGET_PLATFORM']!= self.__env['TARGET_PLATFORM'] or\
            base_env.subst('$CONFIG')!= self.__env.subst('$CONFIG') or\
            base_env['toolchain']!= self.__env['toolchain']:
            if base_env['TARGET_PLATFORM']!= self.__env['TARGET_PLATFORM']:
                diff['TARGET_PLATFORM']=self.__env['TARGET_PLATFORM']
            if base_env['toolchain']!= self.__env['toolchain']:
                diff['toolchain']=self.__env['toolchain']
            if base_env.subst('$CONFIG')!= self.__env.subst('$CONFIG'):
                diff['CONFIG']=self.subst('$CONFIG')
            base_env=self.__settings.Environment(TARGET_PLATFORM=self.__env['TARGET_PLATFORM'],CONFIG=self.__env.subst('$CONFIG'),toolchain=self.__env['TOOLCHAIN'])
        
        diff.update(diff_env(base_env,self.__env))
        if diff !={}:
            import hashlib
            md5=hashlib.md5()  
            md5.update(common.get_content(diff))
            self.__env_diff=diff
            #print diff
            self.__env_diff_sig=md5.hexdigest()
        else:
            self.__env_diff={}
            self.__env_diff_sig=''
        
        #We need to set to the alias value as this is the unique ID used to map data internally
        if self.__alias is None:                
            # we don't have a user provided alias.. make it off the file name
            tmp=self.__env.subst(self.__file)
            tmp=os.path.splitext(os.path.split(tmp)[1])[0] # we only want the file name
            tmp="%s%s"%(tmp,self.__env_diff_sig)
            self.__alias=tmp
            self.__short_alias=tmp
        ##we need to check if this is a sub Parts 
        
        if self.__parent is None:
            # this is the parent so we apply the global Prefix add Postfix values
            self.__alias=self.__env.subst('${ALIAS_PREFIX}%s${ALIAS_POSTFIX}'%self.__short_alias)    
            self.__root=self
            self.__version=version.version('0.0.0')
        else:            
            #we have a parent
            self.__alias=self.__parent.Alias+'.'+self.__short_alias
            self.__root=self.__parent.Root
            if not genid:
                self.__parent.SubParts=self
        if genid: return 
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
        if self.__kw.get('platform_independent',self.__kw.get('platform_indepenent',False)):
            self.__platform_match=platform_info.SystemPlatform('any','any')
            if self.__kw.get('platform_indepenent'):
                api.output.warning_msg('use of "platform_indepenent" is depreciated. Please use "platform_independent" instead.')
        if self.__kw.get('os_independent',self.__kw.get('os_indepenent',False)):
            self.__platform_match.OS='any'
            if self.__kw.get('os_indepenent'):
                api.output.warning_msg('use of "os_indepenent" is depreciated. Please use "os_independent" instead.')
        if self.__kw.get('architecture_independent',self.__kw.get('architecture_indepenent',False)):
            self.__platform_match.ARCH='any'
            if self.__kw.get('architecture_indepenent'):
                api.output.warning_msg('use of "architecture_indepenent" is depreciated. Please use "architecture_independent" instead.')
        
        self.__classic_section=glb.pnodes.Create(section.build_section,self)
        
        self.__is_setup=True
        
    
    #def _update(self,alias=None,name=None,Version=None,file=None,mode=[],vcs_t=None,default=False,
    #        append={},prepend={},create_sdk=True,package_group=None,
    #        **kw):
    #    '''
    #    The logic here is to only add value here until the component is setup
    #    Once it is setup we don't want any value to overide existing values. 
    #    This mean the Part from the user point of view is read-only.
    #    .. need to refactor more ...
    #    '''
    #    if self.__is_setup == False:
    #        self.__alias=alias
    #        self.__name=name
    #        self.__version=version.version(Version)
    #        self.__file=file
    #        self.__mode=common.make_list(mode)
    #        self.__vcs=vcs_t
    #        self.__set_as_default_target=default
    #        self.__append=append
    #        self.__prepend=prepend
    #        self.__create_sdk=create_sdk
    #        self.__kw=kw
    #        self.__package_group=package_group
    #    elif alias==None and name==None and version==None and file==None\
    #        and file==None and mode==[] and vcs_type==None and default==False\
    #        and append=={} and prepend == {} and create_sdk==True and package_group==None:
    #        pass
    #    else:
    #        api.output.error_msg('Part alias = "%s" already has been setup.'%(self.__alias))
    
    def _merge(self,otherobj):
        #turn other object in to this guy the best we can
        otherobj.__dict__=self.__dict__    
            
    def _set_full_depends(self,val):
        """Get the return all(indirect and direct) Parts that this part depends on."""
        self.__full_dependson=val
            
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
        self.__env['PART_LOG_MAPPER']=part_logger.part_logger(self.__env,glb.rpter.console)
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
        self.__env['PART_ROOT_SIG']=self.__root.__env_diff_sig
        if self.__parent is None:
            self.__env['PART_PARENT_NAME']=None
        else:
            self.__env['PART_PARENT_NAME']="${PARTS('"+self.__parent.__alias+"','Name')}"

        ## version info
        self.__env['PART_VERSION']="${PARTS('"+self.__alias+"','Version')}"
        self.__env['PART_SHORT_VERSION']="${PARTS('"+self.__alias+"','ShortVersion')}"
        
        #self.__env['PART_SECTION']='build'
##        # some data we will use for our own DB file
##        if glb.name_alias_map.has_key(alias) == False:
##            glb.name_alias_map[alias]=set()
            
    
    #def __str__(self):
        #pp = pprint.PrettyPrinter(indent=4)
        #return pp.pformat(self.__dict__)

        
    def _map_alias(self):
        ''' This function maps two different of Core Aliases
        One form is to map the given component to all components that it dependson
        The second form is to add all sub-Parts of this component
        '''
        pass
        #vfile=self.__env._MapUnknowns([],self.__file)
        
        # This is the base Alias for a given Part
        #build_alias='${{PART_BUILD_CONCEPT}}${{PART_ALIAS_CONCEPT}}{0}'.format(self.__alias)
        #build_alias_r='${{PART_BUILD_CONCEPT}}${{PART_ALIAS_CONCEPT}}{0}::'.format(self.__alias)
        ## note that InstallXXX and SdkXXX map to this value
        ## new formats will make all targets to this value as well.
        ## build::alias::foo
        #a=self.__env.Alias(build_alias)
        ## build::alias::foo -> build::alias::foo::
        #a1=self.__env.Alias(build_alias_r,a)
        ## map build::alias::foo.sub1:: -> build::alias::foo::
        #if not self.isRoot:
        #    # build::alias::foo.sub:: -> build::alias::foo::
        #    self.__env.Alias('${{PART_BUILD_CONCEPT}}${{PART_ALIAS_CONCEPT}}{0}::'.format(self.Parent.Alias),a1)
        #else:
        #    # build::alias::foo -> build::alias::foo:: -> build::
        #    self.__env.Alias("${PART_BUILD_CONCEPT}",a1)
        #    
        ##add to queue the delayed mapping of high level Alias to other high level alias
        #def_env=SCons.Script.DefaultEnvironment()
        #glb.engine.add_preprocess_logic_queue(functors.map_parts_alias(self.__env))
        ## add call back for latter full mapping of build context
        #glb.engine.add_preprocess_logic_queue(functors.map_build_context(self))
        #
    def _setup_sdk(self):
        return
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
        self.__classic_section._map_targets()
        return
    #    # seems to be an issue for compatibility
    #    utest_call=False
    #    targets=SCons.Script.BUILD_TARGETS
    #    for t in targets:
    #        tmp=target_type(t)
    #        sep_len=len(self.__env.subst("$ALIAS_SEPARTATOR"))
    #        if tmp.concept == self.__env.subst('$BUILD_UTEST_CONCEPT')[:-sep_len] or tmp.concept == self.__env.subst('$RUN_UTEST_CONCEPT')[:-sep_len]:
    #            utest_call=True
    #            break
    #    # if we are not building unit tests
    #    # and this is a classic format
    #    # and this part did not call any SdkXXX or InstallXXX
    #    # then we don't want to define any build actions it may have
    #    if utest_call==False and self._sdk_or_installed_called==False and self._is_classic_format:
    #        pass
    #    else:
    #        self.__env.Alias('${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__alias,list(self.__classic_section.Targets))
        
        
        
    def ReadFile(self):
        # we process the file
        # and check at the end if we processed a new format or an old format
        # error on mixed formats??
        
        if self.__is_read:
            print "\033[1;32m %swas already read"%self.__alias
        
        if self.__is_read==False:
            # final set up for environment
            self.__is_read=None
            env=self.__classic_section.Env            
            ## setup what we want to export
            # global objects
            export_map=glb.parts_objs
            #global object that need to be mapped
            for k,v in glb.parts_objs_env.iteritems():
                export_map[k]=v(env)
            # add the sections
            # we do this when we read as there might have been new sections dynamically added
            #for s in glb.sections:
            #    self.__sections[s.name]=s.Type()(env)
            #export_map.update(self.__sections)
            
            # add the environment
            export_map['env']=env
            env._log_keys=True
            # sort of ugly.. but SCon was to aggressive here in storing state
            try:
                del self.__file._memo['stat']
            except KeyError:
                pass
            bdir=env.Dir(env.subst('$BUILD_DIR'))
            st=time.time()
            sdir=env.Dir(self.__src_path)
            bk_path=sys.path[:]
            sys.path.append(sdir.abspath)
            
            if (glb.engine._build_mode=='build') or (os.path.exists(self.__file.srcnode().abspath)==True):
                if os.path.exists(self.__file.srcnode().abspath)==False:
                    api.output.error_msg('Parts file '+self.__file.srcnode().abspath+" was not found.")
                
                # Call the part file        
                if SCons.Script.GetOption('keep_going'):
                    # don't error is the Parts file has bad data
                    # we just report it and go on
                    # will mostly fail if one needs to build everything
                    # however if i was to build on a component this 
                    # probally will allow me to continue without waiting for the 
                    # one bad component to get fixes
                    try:
                        errors.ResetPartStackFrameInfo()
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
                        api.output.warning_msg("Exception thrown while processing "+self.__file.srcnode().abspath+"\n"+ec_str.getvalue())
                        api.output.print_msg("Will try to continue...")
                        
                else:
                    
                    errors.ResetPartStackFrameInfo()
                    
                    ret=self.__env.SConscript(
                            self.__file,
                            src_dir=sdir,
                            variant_dir=bdir,
                            duplicate=self.__env['duplicate_build'],
                            exports=export_map
                            )
            #print bdir
            #print "*",bdir.srcnode()
            api.output.verbose_msg(['part_read'],'Parts file {0} read time: {1}'.format(self.__file.srcnode().abspath,time.time()-st))
            # we tag the Directory nodes so we can latter sort unknown items faster, by checking the directory ownership
            #pp=pprint.PrettyPrinter()
            #pp.pprint(bdir.__dict__)
            env._log_keys=False
            #common.tag_node_ownership(self.__env,bdir)
            
            # set file as read
            self.__is_read=True
            
            sys.path=bk_path
            
    ## sections based API's
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
        return False
        # reduce
        for name,obj in self.__sections.iteritems():
            # see if the section was even called
            if obj.isSet():
                # if so is it valid() in that non optional phases 
                # have been called
                if not obj.isValid():
                #We have an error
                    api.output.error_msg("Section %s did not define all required phases!\n Define phases are:%s\n Required Phases are:%s"%
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
                api.output.warning_msg("No phase function callbacks for %s.%s in Part %s"%(section,phase,self.__name))
            for i in lst:
                i(self.__env)

            self.__env.fs.chdir(tmp,True)
            self.__cache["%s%scalled"%(section,phase)]=True

    def hasFileChanged(self):
        '''
        Has the file changed in some way. 
        
        The is considered changed if it was modified or the parent was modify.
        '''
        try:
            return self.__cache['hasFileChanged']
        except KeyError:
            data=self.Stored
            # check that stored data is exits
            if data is None:
                self.__cache['hasFileChanged']=True
                self.UpdateReadState(glb.read_load)
                return True
            # Get File Node
            tmp=glb.pnodes.GetNode(data.file['name'],SCons.Node.FS.File)
            if tmp is None:
                self.__cache['hasFileChanged']=True
                self.UpdateReadState(glb.read_load)
                return True
            # does this node look different
            if tmp.changed_since_last_build(tmp,tmp.make_ninfo_from_dict(data.file)):
                self.__cache['hasFileChanged']=True
                self.UpdateReadState(glb.read_load)
                return True
            # does the parent look different
            try:
                if not data.parent.isFileUpToDate():
                    self.__cache['hasFileChanged']=True
                    self.UpdateReadState(glb.read_load)
                    return True
            except AttributeError:
                pass
            self.__cache['hasFileChanged']=False
            return False
    
    def UpdateReadState(self,state):
        if self.__read_state < state:
            self.__read_state = state
            # reset isRead state to allow for cache -> file loading promotions
            # clean up once we clean up sections a bit more to get unit tests working...
            self.__is_read=False 
            self.__sections={}
            
    @property
    def ReadState(self):
        substate=self.SubPartReadState
        self.UpdateReadState(substate)
        return self.__read_state
    
    @property
    def SubPartReadState(self):
        # check that stored data is exits
        data=self.Stored
        if data is None:
            return glb.read_load
        state=glb.read_ignore
        for sub in data.subparts:
            sub=glb.pnodes.GetPNode(sub)
            if sub.ReadState > state:
                state=sub.ReadState 
            if state >= glb.read_load:
                break
        return state
    
    
    ###
    def LoadStoredInfo(self):
        return glb.pnodes.GetStoredPNodeInfo(self)
        #md5=hashlib.md5()
        #md5.update(self.ID)
        #stored_data=datacache.GetCache("pnode-{0}".format(md5.hexdigest()))
        #return stored_data
        
    def StoreStoredInfo(self):
        info=self.GenerateStoredInfo()
        md5=hashlib.md5()
        md5.update(self.ID)
        datacache.StoreData("pnode-{0}".format(md5.hexdigest()),info)
        
    def GenerateStoredInfo(self):
        info=part_info.part_info()
        info.name=self.__name
        info.short_name=self.__short_name
        info.alias=self.__alias
        info.short_alias=self.__short_alias
        info.version=str(self.Version)
        info.root=self.__root
        info.target_platform=str(self.__env['TARGET_PLATFORM'])
        info.config=str(self.__env['CONFIG'])
        info.platform_match=str(self.__platform_match)
        info.package_group=str(self.__package_group) 
        info.mode=self.__mode
        
        #store any subparts aliases
        
        info.subparts=self.__subparts
        
        tmp=[]
        i=self.__parent
        info.parent=i
        while i is not None:
            tmp.append(i)
            i=i.Parent
        info.parents=tmp
        tmp={'build':self.__classic_section}
        tmp.update(self.__sections)
        
        info.sections=tmp
        
        tmp={}
        if self.__file is None:
            pass
            #file['name']=self.Parent._file.srcnode().path# check this
            #file['csig']=self.Parent._file.get_csig()
            #file['timestamp']=self.Parent._file.get_timestamp()
        else:
            tmp['name']=self.__file.srcnode().ID# check this
            tmp['csig']=self.__file.get_csig()
            tmp['timestamp']=self.__file.get_timestamp()
        info.file=tmp
        info.src_path=self.__env.Dir(self.__src_path)
        ##direct sdk file data
        #file={}
        #if self.__sdk_file is None:
        #    file['name']=self.Parent._sdk_file.srcnode().path# check this
        #    file['csig']=self.Parent._sdk_file.get_csig()
        #    file['timestamp']=self.Parent._sdk_file.get_timestamp()
        #    
        #else:
        #    file['name']=self.__sdk_file.srcnode().path# check this
        #    file['csig']=self.__sdk_file.get_csig()
        #    file['timestamp']=self.__sdk_file.get_timestamp()            
        #data['sdkfile']=copy.copy(file)
        #info.sdk_file={} #???
        tmp=[]
        for i in self.__build_context_files:
            if i is None:
                continue
            i=self.__env.File(i)
            # see if node time stamp matches            
            tmp.append(
                    {
                    'name':i.abspath,
                    'csig':i.get_csig(),
                    'timestamp':i.get_timestamp()
                    }
                )
                       
        info.build_context=tmp
        
        # this is config context ( like build but for the config files)
        tmp={}            
        for k,v in self.__config_context_files.iteritems():            
            tmp[k]=[]
            for f in v:
                i=self.__env.File(f)
                # see if node time stamp matches            
                tmp[k].append({
                        'name':i.abspath,
                        'csig':i.get_csig(),
                        'timestamp':i.get_timestamp()
                        })
        info.config_context=tmp
        return info

   
    
    # Depends API
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
    #    api.output.verbose_msg("Duplicate",env.subst($CPPDEFINES))            
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

  
    
    def LoadFromCache(self):
        
        info=self.Stored
        # check that stored data is exits
        #if info is None:
            #self.ReadFile()
            #return
            
       
        self.__alias=info.alias # should be handled by _setup_
        self.__short_alias=info.short_alias # should be handled by _setup_
        self.__root=info.root # should be handled by _setup_
        
        if info.parent:
            # we might not be loading the parent.... so we for set the parent name from cache
            self._set_name(info.short_name,info.parent.Stored.name)
        else:
            self._set_name(info.short_name)
        self.Version=version.version(info.version)
        
        self.__platform_match=info.platform_match # should be handled by _setup_
        self.__package_group=info.package_group # should be handled by _setup_
        self.__mode=info.mode #?? # should be handled by _setup_
        
        self.__subparts=info.subparts
        self.__parent=info.parent # should be handled by _setup_
        # how to deal with this???
        ## need to double check logic for this when full new formats section are working
        self.__sections=info.sections
        #self.__file=info.file # should be handled by _setup_
        #self.__src_path=info.src_path # should be handled by _setup_
        #self.__sdk_file=info.sdk_file # should be handled by _setup_
        
        #info.build_context
        #info.config_context
        
        if not self.isSetup:
            # we don't have a environment created
            # copy the one from the root. it should be good enough
            # for anything we need for part loaded via cache
            self.__env=self.__root.Env.Clone()
            self.__is_setup=True
        
        self.__is_read=True
        self._map_alias()
        
                
        
        
        
        
    def _setup_from_cache_data(self,data):
        '''
        This will setup this part based on data in the cache
        The Part manager will call and create sub part as needed
        The part object should have been created and setup already for this call.
        This function should only have to setup stuff that this component would 
        have exported or outputed that needs to be shared with dependent components
        '''
        
        if self.__is_setup ==False:
            api.output.error_msg("Part object setup from cache data requires part_t object to have been created and setup()")
        # map values that would normally be define in a "new" format
        # such as name and version
        self.ShortName(data['short_name'])
        self.Version(version.version(data['version']))
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
        if self.isRoot:
            self.__cache['root_depends_full']=data['full_root_depends']
            
        



## some util function

def complex_compare(v1,v2):
    
    if type(v1) != type(v2):
        return True
    elif isinstance(v1,SCons.Action.ActionBase):
        return SCons.Action._object_contents(v1) != SCons.Action._object_contents(v2)
    elif isinstance(v1,types.ClassType):
        return True if (v1.__module__,v1.__name__)!=(v2.__module__,v2.__name__) else False
    elif isinstance(v1,types.FunctionType ):
        return True if (v1.__module__,v1.__name__)!=(v2.__module__,v2.__name__) else False
    elif isinstance(v1,dict):
        return v1!=v2
    elif isinstance(v1,list):
        if len(v1) != len(v2):
            return True
        for i,j in zip(v1,v2):
            if complex_compare(i,j):
                return True
            return False
    elif isinstance(v1,types.InstanceType):
        if v1==v2:
            return False
        elif str(v1)==str(v2):
            return False
        return True
    elif  v1!=v2:
        return True
    return False
    

def diff_env(env,env2):
    '''returns set of kv that are different in env2'''
    skip=frozenset(['BUILDERS','ARCHITECTURE','config','CONFIG','PREPROCESS_LOGIC_QUEUE']) # stuff to skip testing
    d1=env.Dictionary()
    d2=env2.Dictionary()
    
    s1=set(d1.keys())
    s2=set(d2.keys())
    
    ret={}
    diff_keys=s1^s2 # what key are not in the common set
    for k in diff_keys:
        if k in skip:
            pass 
        else:
            ret[k]=d1.get(k,d2.get(k,"Not defined in Both environments"))
    common_keys=s1&s2 # what keys both env have
    
    d1.fromkeys(common_keys)
    d2.fromkeys(common_keys)
    
    for k in common_keys:
        if k in skip:
            pass
        elif complex_compare(d1[k],d2[k]):
            ret[k]=d2[k]
    return ret


pnode_manager.manager.RegisterNodeType(part)

