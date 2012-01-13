from .. import glb
from .. import common
from .. import datacache
from .. import api
from .. import target_type
from .. import functors
import pnode
import pnode_manager
import section_info

import SCons.Node

import hashlib
import itertools

import pprint

    
gcnt=0
class section(pnode.pnode):
    """description of class"""
    __slots__=[
        '_ID',
        '__name',
        '__depends', # what we depend on directly (ie explictly), as list (order needed) of ComponentRef objects
        '__full_depends', # what depend on directly and indirectly
        
        '__exports', # value we will export
        '__export_as_depends', #set of values exported item to map as a depends node, when they are referenced in a dependson call
        
        #'__build_context_files', # File that contain code for the builder (or best guess)
        '__target_nodes', # target node for this section
        '__source_nodes', # Source node for this section
        '__installed_files',# anything that gets installed for packaging.
        
        
        '__pobj', # reference to the part containing this section.
        '__env', # the environment for the given section (cloned from Parts object)
        '__user_env_diff',
        '_cache'
    ]
    #

    def __init__(self,pobj=None,ID=None):
        
            self._ID=ID
        
            self.__pobj=pobj
            self.__env={}
            
            self.__depends=[]
            self.__full_depends=[]
        
            self.__exports={}
            self.__export_as_depends=set([]) 
        
            self.__source_nodes = set()
            self.__target_nodes = set()
            self.__installed_files=set()
            self.__user_env_diff={}
        
            self._cache={}
            super(section, self).__init__()
            
    def _setup_(self,pobj,env=None,*lst,**kw):
        self.__pobj=pobj
        if env:
            self.__env=env
        else:
            self.__env=self.__pobj.Env.Clone()
        self.__env['PART_SECTION']=self.Name
        
    @property
    def Name(self):
        raise NotImplementedError
        
    @property
    def Exports(self): #mutable
        return self.__exports
    
    @property
    def ExportAsDepends(self):
        return self.__export_as_depends
    
    @property
    def Targets(self):
        return self.__target_nodes
 
    @property
    def Sources(self):
        return self.__source_nodes
    
    @property
    def InstalledFiles(self):
        return self.__installed_files
    
    @property    
    def Depends(self):
        return self.__depends
    
    @Depends.setter   
    def Depends(self,val):
        common.extend_if_absent(self.__depends,val)
    
    @property    
    def AlwaysBuild(self):
        return self._cache.get("always_build",False)
    
    @AlwaysBuild.setter   
    def AlwaysBuild(self,val):
        self._cache["always_build"]=val
    
    @property
    def FullDepends(self):
        return self.__full_depends
    
    @property
    def Part(self):
        return self.__pobj

    @property
    def Env(self):
        return self.__env
    
    @property
    def UserEnvDiff(self):
        return self.__user_env_diff
    
    
    def _map_targets(self):
        ''' 
        Here we map all known target files that happen in this component 
        to the alias value, to ensure that it is built in case there are actions
        that are no mapped correctly to some action that is mapped to the alias
        such as and sdk or install action
        '''
        
        ## An issue for compatibility.. that I feel should change, but I was out ranked on this.
        #utest_call=False
        #targets=SCons.Script.BUILD_TARGETS
        #for t in targets:
        #    tmp=target_type.target_type(t)
        #    sep_len=len(self.__env.subst("$ALIAS_SEPARTATOR"))
        #    if tmp.concept == self.__env.subst('$BUILD_UTEST_CONCEPT')[:-sep_len] or tmp.concept == self.__env.subst('$RUN_UTEST_CONCEPT')[:-sep_len]:
        #        utest_call=True
        #        break
        ## if we are not building unit tests
        ## and this is a classic format
        ## and this part did not call any SdkXXX or InstallXXX
        ## then we don't want to define any build actions it may have
        #if utest_call==False and self._sdk_or_installed_called==False and self._is_classic_format:
        #    alias_str=self.Env.subst('${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+self.__pobj.Alias)
        #    self.Env.Alias(alias_str,filter(lambda x: isinstance(x,SCons.Node.Alias.Alias) and str(x).startswith(alias_str) ,self.Targets))
        #else:
        # This is the base Alias for a given Part
        alias_str=self.Env.subst('{0}::${{PART_ALIAS_CONCEPT}}{1}'.format(self.Name,self.__pobj.Alias))
        alias_str_r=self.Env.subst('{0}::${{PART_ALIAS_CONCEPT}}{1}::'.format(self.Name,self.__pobj.Alias))
        
        # note that InstallXXX and SdkXXX map to this value
        # new formats will make all targets to this value as well.
        # build::alias::foo
        a=self.__env.Alias(alias_str,filter(lambda x: isinstance(x,SCons.Node.Alias.Alias) and x.ID.startswith(alias_str) ,self.Targets))
                
        # build::alias::foo -> build::alias::foo::
        a1=self.__env.Alias(alias_str_r,a)
        # map build::alias::foo.sub1:: -> build::alias::foo::
        if not self.Part.isRoot:
            # build::alias::foo.sub:: -> build::alias::foo::
            self.__env.Alias('${{PART_BUILD_CONCEPT}}${{PART_ALIAS_CONCEPT}}{0}::'.format(self.Part.Parent.Alias),a1)
        #else:
        # build::alias::foo -> build::alias::foo:: -> build::
        self.__env.Alias("${PART_BUILD_CONCEPT}",a1)
        #add to queue the delayed mapping of high level Alias to other high level alias
        glb.engine.add_preprocess_logic_queue(functors.map_parts_alias(self.__env))
        # add call back for latter full mapping of build context
        glb.engine.add_preprocess_logic_queue(functors.map_build_context(self.Part))

    def _gen_full_parts_depends(self):
        '''a dictionary of everything we dependon (order is lost)
        used to help figure out what to load latter as fast as possible.
        '''
        ret={}
        for d in self.__depends:
            if d.PartRef.hasUniqueMatch:
                pobj=d.PartRef.UniqueMatch
                sec=pobj.Section(d.SectionName)
                sec._add_full_parts_depends(ret)
        return ret
                
    def _add_full_parts_depends(self,data):
        
        try:
        # check if self is added
            if self.__name in data[self.Part.Alias]['sections']:
                #if so return
                return
        except KeyError:
            pass
        
        #else add self
        try:
            data[self.Part.Alias]['sections'].add([self.__name])
        except KeyError:
            data[self.Part.Alias]={
                'sections':set([self.__name]),
                'root_alias':self.Part.Root.Alias
                }
        #add dependents
        for d in self.__depends:
            if d.PartRef.hasUniqueMatch:
                pobj=d.PartRef.UniqueMatch
                sec=pobj.Section(d.SectionName)
                sec._add_full_parts_depends(data)
        
    def esigs(self):
        
        try:
            return self._cache['esigs']
        except KeyError:
            
            # we expand the values here to reduce processing needs latter
            # the the reason we would store this is to speed up build latter
            # ideally this only needs to be expanded in cases of the classic format
            # or cases in which the user added such value to be exported
            export_csig={}
            for k,v in self.__exports.copy().iteritems():
                if common.is_list(v):
                    for i in v[:]:
                        if common.is_string(i) and '$' in i:
                            self.__env.subst(i)
                            
                    new_vals=[]
                    for i in self.__exports[k]:
                        if common.is_string(i) and ('$' in i or i == ''):
                            pass
                        elif isinstance(i,SCons.Node.FS.Base):
                            new_vals.append(i.path)
                        else:
                            new_vals.append(i)
                    if new_vals:
                        self.__exports[k]=new_vals
                    else:
                        del self.__exports[k]
                else:
                    if common.is_string(v) and '$' in v:
                        tmp=self.__env.subst(v)
                        if not tmp:
                            del self.__exports[k]
                            continue
                    elif not v:
                        del self.__exports[k]
                try:
                    
                    md5=hashlib.md5()
                    md5.update(common.get_content(self.__exports[k]))
                    export_csig[k]=md5.hexdigest()  
                except KeyError:
                    pass
                
            self._cache['esigs']=export_csig
        
        return self._cache['esigs']

    def LoadStoredInfo(self):
        tmp=glb.pnodes.GetStoredPNodeInfo(self)
        if tmp.part: # quick sanity check that this is good data
            return tmp
        return None
                
    #def StoreStoredInfo(self):
    #    info=self.GenerateStoredInfo()
    #    md5=hashlib.md5()
    #    md5.update(self.ID)
    #    datacache.StoreData("pnode-{0}".format(md5.hexdigest()),info)

    def GenerateStoredInfo(self):
        info=section_info.section_info()
               
        info.part=self.Part
        info.name=self.Name
        
        info.esigs=self.esigs()
        info.exports=self.__exports        
        
        ## data about what this depends on we want the direct depend here
        ## as this will allow us to speed up incremential build latter
        tmp=[]
        # to get the dependance sig
        for d in self.__depends:
            tmp.append({
                'PartRef':str(d.PartRef.Target),
                'SectionName':d.SectionName,
                'Part':d.Part,
                'Requires':d.Requires,
                'rsigs':d.rsigs(),
                'rsig':d.rsig(),
                'Section':d.Section,
            })
            
        info.user_env_diff=self.__user_env_diff
        info.dependson=tmp
        # these are items that are exported, and noted as a map_as_depends in ExportItem()
        info.exported_requirements=self.ExportAsDepends
        return info
    
    def LoadFromCache(self):
        info = self.Stored
        # get out owning part
        self.__part=info.part
        self.__env=self.__part.Env.Clone()
        self.__env['PART_SECTION']=self.Name
        self.__user_env_diff=info.user_env_diff
        self.__env.Replace(**self.__user_env_diff)
        # import the values we export
        # We assume these are fully resolved so we don't need to get any data from anything this
        # section would have depended on
        self.__exports=info.exports 
        
        # need to map these items as Aliases
        self.__export_as_depends=info.exported_requirements 
        for export in self.__export_as_depends:
            self.__env.Alias("{0}::alias::{1}::{2}".format(self.Name,self.__part.Alias,export),self.__exports[export])
            
    def hasPartFileChanged(self):
        '''Has the Part File defining this section changed in some way
        
        This can include if the Parent Parts file changed, as this could change 
        what the children Part files would define.
        '''
        return self.Stored.part.hasFileChanged()
    
    def TagDirectDependAsLoad(self,load_manager):
        try:
            return self._cache['TagDirectDependAsLoad']
        except KeyError:
            # get stored data
            stored_data=self.Stored
            
            if stored_data is None:
                self._cache['TagDirectDependAsLoad']=False
                #return False to signal there was a cache issue
                return False
            # set our state
            self.ReadState=glb.load_file
                            
            for dep in stored_data.dependson:
                sec=dep['Section']
                if not sec.TagDirectDependAsLoad(load_manager):
                    self._cache['TagDirectDependAsLoad']=False
                    return False
            self._cache['TagDirectDependAsLoad']=True
            # set our root parts
            try:
                try:
                    tmp=stored_data.part.Stored.parent.Stored.sections[self.Name]
                except KeyError:
                    tmp=stored_data.part.Stored.parent.Stored.sections['build']
                if not tmp.TagDirectDependAsLoad(load_manager):
                    self._cache['TagDirectDependAsLoad']=False
                    return False
            except AttributeError:
                pass
            return self._cache['TagDirectDependAsLoad']
        
    
    @property
    def ReadState(self):
        if self.__pobj is None:
            return self.Stored.part.ReadState
        return self.__pobj.ReadState
    
    @ReadState.setter
    def ReadState(self,state):
        if self.__pobj is None:
            self.Stored.part.UpdateReadState(state)
        else:
            self.Part.UpdateReadState(state)
    
    #
    #def Serialize(self):
    #    # store what we export
    #    data={}
    #    
    #    data['exports']=self.__exports
    #    #
    #    ## this is for recreating a part from cache as these values are
    #    ## set by the user and don't exist by default
    #    #data['env_exports']=self._user_env_diff
    #    ## data about what this depends on we want the direct depend here
    #    ## as this will allow us to speed up incremential build latter
    #    tmp=[]
    #    for d in self.__depends:
    #        tmp.append({
    #            'PartRef':str(d.PartRef.Target),
    #            'Section':d.SectionName,
    #            'requires':d.Requires.Serialize()               
    #        })
    #    data['dependson']=tmp
    #    # data about what this depends on used to help with startup time
    #    # this contains the full set of direct dependancies needed for 
    #    # this section to be processed. It does not contain 
    #    # any subparts that might be needed on the side to load correct.
    #    data['full_depends']=self._gen_full_parts_depends()
    #    
    #    
    #    
    #    #store all known "group" Alias that are part of this section
    #    tmp=set()
    #    temp=[self.Env.subst('${{PART_BUILD_CONCEPT}}${{PART_ALIAS_CONCEPT}}${{ALIAS}}::{0}'.format(l)) for l in self.ExportAsDepends]
    #    for i in filter(lambda x: isinstance(x,SCons.Node.Alias.Alias),self.__target_nodes):
    #        if i.name in temp:
    #            tmp.add(i)
    #    data['aliases']=tmp
    #    
    #    #store all known node that are mapped to this component as
    #    #a list of strings. we use the SCons DB to store the important data
    #    tmp=[]
    #    for i in filter(lambda x: not isinstance(x,SCons.Node.Alias.Alias),self.__target_nodes):
    #        i.disambiguate()
    #        ## see if node time stamp matches
    #        #dbentry=i.get_stored_info()
    #        #
    #        ##import pprint
    #        ##pp = pprint.PrettyPrinter()
    #        #
    #        #
    #        #if getattr(dbentry,'ninfo',None) is None:
    #        #    # if here this was not built yet
    #        #    tmpd=i.path # use path if we want to use SCons DB
    #        #    #tmpd={'name':i.path}
    #        #    tmp.append(tmpd)
    #        #else:
    #        #    ninfo=dbentry.ninfo
    #        #    #print pp.pprint(dbentry.binfo.__dict__)
    #        #    #tmpd=i.path # use path if we want to use SCons DB
    #        #    tmpd={
    #        #    'name':i.path
    #        #    }
    #        #    tmpd.update(ninfo.__dict__)
    #        #    tmp.append(tmpd)
    #        tmp.append(i.path)
    #    data['targets']=tmp
    #    tmp=[]
    #    for i in filter(lambda x: not isinstance(x,SCons.Node.Alias.Alias),self.__source_nodes):
    #        i.disambiguate()
    #        # see if node time stamp matches
    #        dbentry=i.get_stored_info()
    #        if i.has_builder()==False or getattr(dbentry,'ninfo',None) is None:
    #            # this should be some source node
    #            # it might have been a target node as well, but since it has no builder
    #            # it should be source only
    #            
    #            if isinstance(i,SCons.Node.FS.Base):
    #                tmp.append(
    #                        #{
    #                        #'name':i.path,
    #                        #'csig':i.get_csig(),
    #                        #'timestamp':i.get_timestamp()
    #                        #}
    #                        i.path
    #                    )
    #            elif isinstance(i,SCons.Node.Python.Value):
    #                tmp.append(
    #                        i.value
    #                        #{
    #                        #'type':'Value',
    #                        #'name':i.value,
    #                        #'csig':i.get_csig(),
    #                        #}
    #                    )
    #            
    #        
    #    data['sources']=tmp
    #    return data
    



class build_section(section):
    
    def __init__(self,pobj=None,ID=None):
        super(build_section, self).__init__(pobj,ID)
        
    @staticmethod
    def _process_arg(pobj=None,**kw):
        id = kw.get('ID')
        setup=False
        if pobj:
            id="{1}::{0}".format(pobj.ID,'build')
            setup=True
        elif id is None:
            raise ValueError , "Invalid arguments values when creating section type"
        
        return id,setup    
        
    @section.ID.getter
    def ID(self):
        if self._ID is None:
            self._ID="{1}::{0}".format(self.Part.ID,self.Name)
        return self._ID
    
    @section.Name.getter
    def Name(self):
        return "build"
    

class utest_section(section):
    
    def __init__(self,pobj=None,ID=None,env=None):
        super(utest_section, self).__init__(pobj,ID)
        
    @staticmethod
    def _process_arg(pobj=None,**kw):
        id = kw.get('ID')
        setup=False
        if pobj:
            id="{1}::{0}".format(pobj.ID,'utest')
            setup=True
        elif id is None:
            raise ValueError , "Invalid arguments values when creating section type"
        
        return id,setup    
        
    @section.ID.getter
    def ID(self):
        if self._ID is None:
            self._ID="{1}::{0}".format(self.Part.ID,self.Name)
        return self._ID
    
    @section.Name.getter
    def Name(self):
        return "utest"



pnode_manager.manager.RegisterNodeType(build_section)
pnode_manager.manager.RegisterNodeType(utest_section)

#glb.pnodes.AddFactory(build_section,lambda id:buildsectionfactory(ID=id))
