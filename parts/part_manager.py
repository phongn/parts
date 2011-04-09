
import glb
import common
import errors
import pnode.part
import api.output
import datacache
import node_helpers
import platform_info
import vcs
import version
from target_type import target_type


import SCons.Script
import time
import os
import copy

import SCons.Job


def pcmp(x,y):
            
    return cmp(x._order_value,y._order_value)


def scmp(x,y):
    xp=x.Stored.part.Stored.root
    yp=y.Stored.part.Stored.root
    return cmp(xp._order_value,yp._order_value)


class load_section_task(object):
    ''' 
    
    '''
    def __init__(self,sec,pmgr,taskmaster):
        self.__section = sec
        self.__pmgr = pmgr
        self.__failed=False
        self.__taskmaster=taskmaster
    
    @property
    def Section(self):
        ''' '''
        return self.__section
            
    def prepare(self):
        ''' this is called before the task starts.
        
        Set up any logic or to figure out if anything should execute.
        '''
        pass
        
    def needs_execute(self):
        ''' reports if anything should execute'''
        return 1
    
    def execute(self):
        ''' '''
        try:
            self.__pmgr.LoadSection(self.Section)
            #    self.failed()
        except PartRuntimeError, e:
            buildError = SCons.Errors.convert_to_BuildError(e)
            buildError.node = self.__sections.Part.File
            buildError.exc_info = sys.exc_info()
            raise buildError
        #except:
        #    
        #    import traceback,StringIO
        #    #ec_str=StringIO.StringIO()
        #    traceback.print_exc()#file=ec_str)
        #    raise
        
    def exception_set(self,exception=None):
        self.__failed=True
        
    def failed(self):
        #if self.__failed:
        api.output.error_msg("Load task failed for Part %s"%self.__section.ID,show_stack=False,exit=False)
        self.__taskmaster.stop()
        
    def executed(self):
        ''' this gets called when everything execute() correctly'''
        pass

    def postprocess(self):
        ''' this always gets called after the task ran, failed or not'''
        pass
        

class load_parts_task(object):
    ''' 
    
    '''
    def __init__(self,pobj,pmgr,taskmaster):
        self.__pobj= pobj
        self.__pmgr = pmgr
        self.__failed=False
        self.__taskmaster=taskmaster
    
    @property
    def Part(self):
        ''' '''
        return self.__pobj
            
    def prepare(self):
        ''' this is called before the task starts.
        
        Set up any logic or to figure out if anything should execute.
        '''
        pass
        
    def needs_execute(self):
        ''' reports if anything should execute'''
        return 1
    
    def execute(self):
        ''' '''
        try:
            self.__pmgr.LoadPart(self.__pobj)
            #    self.failed()
        except PartRuntimeError, e:
            buildError = SCons.Errors.convert_to_BuildError(e)
            buildError.node = self.__sections.Part.File
            buildError.exc_info = sys.exc_info()
            raise buildError
        #except:
        #    
        #    import traceback,StringIO
        #    #ec_str=StringIO.StringIO()
        #    traceback.print_exc()#file=ec_str)
        #    raise
        
    def exception_set(self,exception=None):
        self.__failed=True
        
    def failed(self):
        #if self.__failed:
        api.output.error_msg("Load task failed for Part %s"%self.__section.ID,show_stack=False,exit=False)
        self.__taskmaster.stop()
        
    def executed(self):
        ''' this gets called when everything execute() correctly'''
        pass

    def postprocess(self):
        ''' this always gets called after the task ran, failed or not'''
        pass


## set of task master loaders
class load_all_roots_loader(object): #task_master type
    '''
    
    '''
    def __init__(self,pmanager):
        
        self.pmgr=pmanager
        self._section_from_cache=set() # all the section we need to load from cache
        self._parts_to_read=set() # all the parts we have to readin
        
        
    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t
    
    def stop(self):
        self.__stopped=True
        self.__i= -1
    
    @property
    def Stopped(self):
        return self.__stopped
        
    def cleanup(self):
        pass
        
    def _has_tasks(self):
        return self.__tasks != []
        
    def DefineTasksList(self):
        
        for v in self.pmgr.parts.values():
            self.__tasks.append(load_parts_task(v,self.pmgr,self))
            
    def __call__(self):
        parts_to_load=self.pmgr.parts.values()
        parts_to_load.sort(pcmp)
        for pobj in parts_to_load:
            self.pmgr.LoadPart(pobj)
        # we are loading everything..so we don't want to exit early
        return False
        


class direct_depends_loader(object): #task_master type
    '''
    figures our what we need load. basic logic is to test the dependents first
    Then the container defining that and move inwards (ie part->section->node)
    '''
    def __init__(self,targets,pmanager):
        # set of sections to build 
        #.. assume nodes are filtered out if ther did not expand to a section
        self.sections=targets 
        self.pmgr=pmanager
        self._section_from_cache=set() # all the section we need to load from cache
        self._parts_to_read=set() # all the parts we have to readin
        
        
    @property
    def hasStored(self):
        return self.pmgr.hasStored
    
    @hasStored.setter
    def hasStored(self,value):
        if value==False:
            raise errors.LoadStoredError
             
    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t
    
    def stop(self):
        self.__stopped=True
        self.__i= -1
    
    @property
    def Stopped(self):
        return self.__stopped
        
    def cleanup(self):
        pass
        
    def _has_tasks(self):
        return self.__tasks != []
        
    def DefineTasksList(self):
        
        if sec.TagDirectDependAsLoad()==False:
            self.pmgr.hasStored=False
            return False
        
        for pobj in self.pmgr.parts.values():
            if pobj.ReadState==glb.read_load:
                self.__tasks.append(load_parts_task(pobj,self.pmgr,self))
            
    
    def __call__(self): 
        # we are force loading files here so 
        # we can exit early
        for sec in self.sections:
            if sec.TagDirectDependAsLoad(self.pmgr)==False:
                self.pmgr.hasStored=False
                return False
        
        parts_to_load=self.pmgr.parts.values()
        parts_to_load.sort(pcmp)
        for pobj in parts_to_load:
            if pobj.ReadState==glb.read_load:
                self.pmgr.LoadPart(pobj)
        return False        

class section_changed_loader(object): #task_master type
    '''
    figures our what we need load. basic logic is to test the dependents first
    Then the container defining that and move inwards (ie part->section->node)
    '''
    def __init__(self,targets,pmanager):
        # set of sections to build 
        #.. assume nodes are filtered out if ther did not expand to a section
        self.sections=targets 
        self.pmgr=pmanager
        self._section_from_cache=set() # all the section we need to load from cache
        self._section_to_read=set() # all the section we have to readin
        
        
    @property
    def hasStored(self):
        return self.pmgr.hasStored
    
    @hasStored.setter
    def hasStored(self,value):
        if value==False:
            raise errors.LoadStoredError
             
    def LoadSection(self,sec):
        sec.ReadState=glb.read_load
        #see if the section is in the set of stuff we are loading from cache
        if sec in self._section_from_cache:
            self._section_from_cache.remove(sec)
        
        # deal with the fact we want to load this sections part file    
        self._section_to_read.add(sec)
        
        #tag dependents that are not in ignore state to a cache state
        for dep in sec.Stored.dependson:
            tsec=dep['Section']
            if tsec.ReadState == glb.read_ignore:
                # set the cache state
                tsec.ReadState=glb.read_cache
                self._section_from_cache.add(tsec)
                
        #if this sec part is not a root we need to tag the parents depends as cache
        while sec.Stored.part.Stored.parent:
            sec=sec.Stored.part.Stored.parent.Stored.sections[sec.Name]
            for dep in sec.Stored.dependson:
                tsec=dep['Section']
                if tsec.ReadState == glb.read_ignore:
                    # set the cache state
                    tsec.ReadState=glb.read_cache
                    self._section_from_cache.add(tsec)
            
        
    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t
    
    def stop(self):
        self.__stopped=True
        self.__i= -1
    
    @property
    def Stopped(self):
        return self.__stopped
        
    def cleanup(self):
        pass
        
    def _has_tasks(self):
        return self.__tasks != []
        
    def DefineTasksList(self):
        try:
            for sec in self.sections:
                stt=time.time()
                tmp = sec.hasSectionChanged(self)
                #print sec.ID,"Changed!" if tmp else "unchanged", time.time()-stt
                
        except errors.LoadStoredError:
            print "Stored data is missing"
            self.pmgr.hasStored=False
            
        for i in self._parts_to_read:
            self.__tasks.append(load_parts_task(i,self.pmgr,self))
            
        for i in self._section_from_cache:
            self.__tasks.append(load_section_task(i,self.pmgr,self))
            
    
    def __call__(self): 
        up_to_date=True
        try:
            for sec in self.sections:
                stt=time.time()
                tmp=sec.hasSectionChanged(self)
                #print sec.ID,"Changed!" if tmp else "unchanged", time.time()-stt
                if tmp:#sec.hasSectionChanged(self):
                    up_to_date=False
                    # we have changed so we add our self to the target list. This can happen when a Scons node
                    # was used as a target and it depends on this component
                    SCons.Script.BUILD_TARGETS.append("{0}::{1}".format(sec.Name,sec.Stored.part.Stored.name))
                
        except errors.LoadStoredError:
            print "Stored data is missing"
            self.pmgr.hasStored=False
            return False
        
        #print "loading from file"
        #for i in self._section_to_read:
        #    print " ",i
        #print "loading from cache"
        #for i in self._section_from_cache:
        #    print " ",i
        
        sections_to_load = list(self._section_from_cache)+list(self._section_to_read)
        
        sections_to_load.sort(scmp)
        for sec in sections_to_load:
            self.pmgr.LoadSection(sec)
        
        #for i in self._section_to_read:
        #    self.pmgr.LoadSection(i)
        #
        #for i in self._section_from_cache:
        #    self.pmgr.LoadSection(i)
        
        return up_to_date
  
    
class part_manager(object):
    
    def __init__(self):
        self.sections=glb.sections
        self.parts={} # a dictionary of all parts objects by there alias value
        self.__name_to_alias={} #a dictionary of a known Parts name and possible alias that match
        self.__to_map_parts=[] # stuff that needs to be mapped, else it is wasted space
        self.__hasStored= SCons.Script.GetOption("parts_cache") # used to help prevent wasting time on cases of incomplete cache data
        self.__part_count=0 # number of parts we have defined.. 
        
        glb.engine.CacheDataEvent+=self.Store
    
    def map_targets_stored_pnodes(self,targets):
        '''Turn the targets into a list of pnodes or Node ( given if can't be mapped to a Pnode) objects'''
        ret=[] # the new target list
        ret_nodes=[]
        name_matches=None
        
        stored_data=datacache.GetCache("part_map")
        
        if stored_data is None:
            self.__hasStored=False
            api.output.verbose_msg(['target_mapping'],"part_map data cache did not load, Loading everything")
            return
        stored_name_to_alias=stored_data['name_to_alias']
            
        for t in SCons.Script.BUILD_TARGETS:
            if isinstance(t,SCons.Node.Node):
                api.output.verbose_msg(['target_mapping'],"Target is SCons node")
                tmp=[]
                self.add_stored_node_info(t,tmp)
                ret+=tmp
                ret_nodes.append((t,tmp))
                if not self.__hasStored: 
                    api.output.verbose_msg(['target_mapping'],'No Stored info found for "{0}", Loading everything'.format(t.ID))
                    return
            else:
                #This is a string to a target we need to figure out
                tobj=target_type(t)
                # first see if this is ambiguous
                # ie this is something like 'foo'
                # we don't know if this is a name::foo, alias::foo or a directory called foo, etc
                if not tobj.isPartTarget:
                    # we want to figure out based on stored information is this something we should know about
                    known_parts=stored_data['known_parts']
                    ta=target_type("alias::"+str(t))
                    tn=target_type("name::"+str(t))
                    
                    # this might be a name
                    name_matches={}                       
                    try:
                        for k,pobj in stored_name_to_alias[tn.name].iteritems():
                            try:
                                name_matches[pobj.Stored.root.ID].add(pobj)
                            except KeyError:
                                name_matches[pobj.Stored.root.ID]=set([pobj]) 
                    except KeyError:
                        pass
                    if name_matches != {}:
                        # we have some matches
                        api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a known name'.format(tn.name))
                        tobj=tn
                    #see if this is an alias we have
                    elif glb.pnodes.isKnownPNode(ta.alias):# known_parts.keys():
                        # this looks like an alias we should know about
                        api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a known alias'.format(t))
                        tobj=ta
                    elif glb.pnodes.isKnownNodeStored(t):
                        node=glb.pnodes.GetNode(t)
                        tmp=[]
                        self.add_stored_node_info(node,tmp)
                        ret+=tmp
                        ret_nodes.append((node,tmp))
                        if not self.__hasStored: 
                            api.output.verbose_msg(['target_mapping'],'Target: "{0}" missing stored data, Loading everything'.format(t))
                            return
                        api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a known SCons node'.format(t))
                        continue
                    else:
                        # we don't know this.. assume we have to load everything
                        api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a not known, Loading everything')
                        return None
                
                #process the target node into Alias nodes                
                if tobj.concept:
                    concept=tobj.concept
                else:
                    concept='build'
                    tobj.concept=concept
                if tobj.all:
                    # add the concept:: alias as we define this
                    tmp=glb.engine.def_env.Alias(concept+"::")[0]
                    api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a concept'.format(tobj))
                    self.add_stored_node_info(tmp,ret)
                    if not self.__hasStored: 
                        api.output.verbose_msg(['target_mapping'],'No stored information found for "{0}", Loading everything'.format(tobj))
                        return
                elif tobj.alias:
                    # add the concept::alias section as we define this
                    # get pobj
                    if glb.pnodes.isKnownPNodeStored(tobj.alias): 
                        pobj=glb.pnodes.GetPNode(tobj.alias)
                        # get stored section
                        tmp=pobj.Stored.sections[tobj.concept]
                        api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a Alias'.format(tobj))
                        ret.append(tmp)
                    else:
                        # this is not known.. backout
                        api.output.verbose_msg(['target_mapping'],'No stored information found for "{0}", Loading everything'.format(tobj))
                        return None
                elif tobj.name:
                    api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a name'.format(tobj))
                    if name_matches is None:
                        name_matches={}
                        for pobj in stored_name_to_alias[tn.name]:
                            try:
                                name_matches[pobj.Stored.root.ID].add(pobj)
                            except AttributeError:
                                name_matches[pobj.Stored.root.ID]=set([pobj]) 
                    if name_matches=={}:
                        api.output.verbose_msg(['target_mapping'],'No matches found for name, Loading everything'.format(tobj))
                        return None # we don't have any known found values.. backout
                    root_aliases = name_matches.keys()
                    # try to process known values
                    ## keep in mind this assume classic formats
                    ## and it will get stuff wrong.. 
                    ## what it can get wrong is loading stuff we might not build
                    ## and even possiblity not loading stuff ( ie in more complex cases of sub-parts with lots of Customization )
                    ## however common simple cases should be ok ( ie no sub-parts or no to minimum Customization form the default settings)
                    ## ideally setup with only new formats will not have these issues, as we can read first, and get need info
                    for k,v in tobj.properties.iteritems():
                        for ID in root_aliases:
                            pobj= self._from_alias(ID)
                            if k == 'version':
                                if common.is_string(v):
                                    v=version.version_range(v+'.*')
                                if pobj.Version not in v:
                                    del name_matches[ID]
                            elif k in ['target','target-platform','target_platform']:
                                if pobj.Env['TARGET_PLATFORM'] != v:
                                    del name_matches[ID]
                            elif k in ['cfg','config','build-config','build_config']:
                                if not pobj.Env.isConfigBasedOn(v):
                                    del name_matches[ID]
                            elif k == 'mode':
                                mv=v.split(',')
                                for v in mv:
                                    if v not in pobj._mode:
                                        del name_matches[ID]
                                        break
                            else:
                                #look up in the parts environment
                                try:
                                    if pobj.Env[k] != v:
                                        del name_matches[ID]
                                except KeyError:
                                    del name_matches[ID]
                    if name_matches=={}:
                        api.output.verbose_msg(['target_mapping'],'No matched found for "{0}", Loading everything'.format(tobj))
                        return None
                    for RID,pobjs in name_matches.iteritems():
                        for pobj in pobjs:
                            # get stored section
                            tmp=pobj.Stored.sections[tobj.concept]
                            ret.append(tmp)
        
        return (ret,ret_nodes)

   
    def LoadSection(self,sec):
        
        # to load a section we have to make sure to the 
        # Part defining this section has been read in correctly
        pobj=sec.Stored.part
        if not pobj.isRead and pobj.isSetup:
            # we can load this without issue
            #print "LOADING PART",pobj.ID
            self.LoadPart(pobj)
        elif not pobj.isRead and not pobj.isSetup:
            #print "LOADING PART from cache",pobj.ID
            # in this case we want to load the parent and the simular section
            #self.LoadSection(pobj.Stored.parent.Stored.sections[sec.Name])
            # read in the Parts
            self.LoadPart(pobj)
            
            
            #pobj.LoadFromCache()
            #self._add_part(pobj) 
            #sec.LoadFromCache()
            #try loading again
            #self.LoadSection(sec)
        if pobj.ReadState == glb.read_cache:
            #print "LOADING SECTION",sec.ID
            sec.LoadFromCache()
        
        
    def LoadPart(self,pobj):
        part_file_load_time=time.time()
        #see if this part is setup
        if pobj.isSetup:
            # it is setup, so the parent has been read in
            
            if not pobj.isRead and (pobj.ReadState == glb.read_load or self.__hasStored==False):
                #read in the data fully
                api.output.verbose_msg(['loading'],"Loading from file: {0}".format(pobj.ID))
                pobj.UpdateReadState(glb.read_load)
                pobj.ReadFile()
                # move this?? This maps any unknown Part() calls that should be rebound to a parts object
                self._clean_unknown(pobj)
                #map the aliases
                #pobj._map_alias()
                #pobj._setup_sdk()
                #pobj._map_targets()
             
                # figure out if this part is new style or old style
                valid_sec=self.hasValidSection(pobj)
                if not pobj._hasTargetFiles() and valid_sec:
                    # new format
                    pobj.Format='new'
                    has_valid_sections=True
                elif pobj._hasTargetFiles() and valid_sec:
                    # mixed.. not sure what to do yet with this...
                    #print "mixed",p.Name
                    pass
                elif pobj._hasTargetFiles() and not valid_sec:
                    #old format
                    # if old format we have also processed the part
                    pobj.Format='classic'
                    pobj._map_alias()
                    pobj._setup_sdk()
                    pobj._map_targets()
                else:
                    # did not define anything to do?
                    # could be a root parts with subparts?
                    pobj.Format='unknown'
                    pobj._map_alias()
                    pobj._setup_sdk()
                    #print "unknown",p.Name
            #api.output.verbose_msg(['loading'],"{0:60}[{1:.2f} secs]".format(msg,(time.time()-part_file_load_time)))
            #api.output.console_msg(" Loading %3.2f%% %s \033[K"%((cnt/total*100),msg))
            #cnt+=1
                
            elif not pobj.isRead and pobj.ReadState == glb.read_cache:
                api.output.verbose_msg(['loading'],"Loading from cache: {0}".format(pobj.ID))
                pobj.LoadFromCache()
                self._add_part(pobj) 
                
            else:
                #print "Ignoring the loading of Parts:",pobj.ID,pobj.isRead,pobj.ReadState
                api.output.verbose_msg(['loading'],"not loading: {0}".format(pobj.ID))
        else:
            # we are trying to load some sub-part that has not had it parent read in yet
            # there are two cases for this parent.. it is will be read-in via cache 
            # or via reading the Parts file.
            #If the Parts parents is not read yet. we want to read it
            #print "**** part is not setup:",pobj.ID
            if not pobj.Stored.parent.isRead:
                #print "**** trying to load parent:",pobj.Stored.parent
                self.LoadPart(pobj.Stored.parent)
                
            #Given that it is read at this point. we need to check to see if we are read
            # given that parent should have loaded.. we should be loaded as well
            # if we are not and we are to be read in as cache ( what we should see if not read-in yet)
            # we want to load this part from cache
            if not pobj.isRead and pobj.ReadState == glb.read_cache:
                #print "**** load from cache",pobj.ID
                api.output.verbose_msg(['loading'],"Loading From cache: {0}".format(pobj.ID))
                pobj.LoadFromCache()
                self._add_part(pobj) 
            # it is possible a loader gave us a part we want to ignore    
            elif not pobj.isRead and pobj.ReadState == glb.read_ignore:
                #print "Ignoring the loading of Parts:",pobj.ID,pobj.isRead,pobj.ReadState
                api.output.verbose_msg(['loading'],"not loading: {0}".format(pobj.ID))
            elif not pobj.isRead:
                # if we are here.. something is wrong
                #print pobj,pobj.isRead,pobj.ReadState
                api.output.error_msg("unexpected load case")
        if pobj.ReadState != glb.read_ignore:
            api.output.verbose_msg(['loading'],"Loaded {0:60}[{1:.2f} secs]".format(pobj.ID,(time.time()-part_file_load_time)))
                
   
    def _define_sub_part(self,env,alias,parts_file,mode=[],vcs_type=None,
            default=False,append={},prepend={},create_sdk=True,package_group=None,
            **kw):
            
        parent_part=self._from_env(env)
        # here we setup stuff we need to pass down from the parent
        new_kw={}
        new_append={}
        new_prepend={}
        new_kw.update(parent_part._kw)
        new_append.update(parent_part._append)
        new_prepend.update(parent_part._prepend)
        if package_group is None:
            package_group=parent_part.PackageGroup
        if mode==[]:
            mode=parent_part.Mode
        new_kw.update(kw)
        if 'parent_part' in new_kw:
            del new_kw['parent_part']
        new_append.update(append)
        new_prepend.update(prepend)
        tmp=glb.pnodes.Create(pnode.part.part,alias=alias,file=parts_file,mode=mode,vcs_t=vcs_type,
                        default=default,append=new_append,prepend=new_prepend,
                        create_sdk=create_sdk,package_group=package_group,
                        parent_part=parent_part,**new_kw)
        # setup new object
        #tmp._setup_()
        # add to set of known parts
        if tmp.isSetup:
            # see if this should be readin
            self._add_part(tmp)   
            self.LoadPart(tmp)
        else:
            print tmp.ID,"is NOT SETUP!!!!!!!!"
        
        return tmp
    
    def map_scons_target_list(self,uptodate):
        ''' here we try to map the Parts target values to values SCons can build'''
        
        # trying to translate based on everything being read in
        new_list=[] # the new target list
        api.output.verbose_msg(['loading'],"Orginal BUILD_TARGETS: %s"%SCons.Script.BUILD_TARGETS)
        
        for t in SCons.Script.BUILD_TARGETS:
            tobj=target_type(t)
            # first see if this is ambiguous
            if not tobj.isPartTarget:
                # we are not sure
                # first we try to see if the name can be matched
                ta=target_type("alias::"+str(t))
                tn=target_type("name::"+str(t))
                if self.__name_to_alias.get(tn.name):
                    #we are sure this is a Parts value
                    tobj=tn
                # see if this is an alias value
                elif self.parts.get(ta.alias):
                    #we are sure this is a Parts value
                    tobj=ta
                else:
                    #we are sure this is a SCons value
                    new_list.append(t)
            
            
            #we are that this is a Part target format
            # see what concept is defined
            if tobj.concept:
                concept=tobj.concept
            else:
                concept='build'
            if tobj.all:
                # add the concept:: alias as we define this
                new_list.append(concept+"::")
            elif tobj.alias:
                # add the concept::alias alias as we define this
                new_list.append(concept+"::alias::"+tobj.alias)
            elif tobj.name:
                #This case can have multipul matches
                # get a list of known alias that have this name
                alias_lst=self.__name_to_alias.get(tobj.name)
                
                if alias_lst is None:
                    #error we don't have a target called this to build
                    api.output.error_msg("Unknown name: %s"%(tobj.name),show_stack=False)
                #filter out any of these that don't match the properties
                
                for k,v in tobj.properties.iteritems():
                    for i in alias_lst.copy():
                        pobj= self._from_alias(i)
                        
                        if k == 'version':
                            if common.is_string(v):
                                v=version.version_range(v+'.*')
                            if pobj.Version not in v:
                                alias_lst.remove(i)
                        elif k in ['target','target-platform','target_platform']:
                            if pobj.Env['TARGET_PLATFORM'] != v:
                                alias_lst.remove(i)
                        elif k in ['cfg','config','build-config','build_config']:
                            if not pobj.Env.isConfigBasedOn(v):
                                alias_lst.remove(i)
                        elif k == 'mode':
                            mv=v.split(',')
                            for v in mv:
                                if v not in pobj._mode:
                                    alias_lst.remove(i)
                                    break
                        else:
                            #look up in the parts environment
                            try:
                                if pobj.Env[k] != v:
                                    alias_lst.remove(i)
                            except KeyError:
                                alias_lst.remove(i)
                if alias_lst==set():
                    api.output.error_msg('"%s" did not map to any defined Parts'%t)
                for i in alias_lst:
                    new_list.append(concept+"::alias::"+i)
        SCons.Script.BUILD_TARGETS=new_list
        api.output.verbose_msg(['loading'],"Updated BUILD_TARGETS: %s"%SCons.Script.BUILD_TARGETS)
    
    
    def ProcessParts(self):
        ''' 
        This function will process all the Parts object based on the targets
        '''
        
        #######    
        ##update the disk
        ##is everything up to date on disk update file on disk?
        ## if not we need to update it
        api.output.print_msg("Updating disk")
        self.UpdateOnDisk( self.parts.values() )
        
        skip_update_check=True
        nodes_up_to_date=True
        has_valid_sections=False
        targets=SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets == []:
            return 
        sections_to_process=[]
        nodes=[]
        if self.__hasStored:
            ## map target to a part alias or a scons node via mapping node info from our DB of all known nodes
            tmp=self.map_targets_stored_pnodes(targets)
            # check to see if any SCons nodes in the targets are out of date
            if tmp:
                # break up the returned data into sections, and SCons nodes
                sections_to_process,nodes=tmp
                
            # see if we have any nodes
            # and see if they are out of date
            for node,sections in nodes:
                # need to review this again..
                # this is only the Part like check
                # it does not see changes in Environment
                if node.pisUpToDate == False:
                    for s in sections:
                        nodes_up_to_date=False
                        #set the read state to be read ( change to cache later?)
                        s.ReadState=glb.read_load
                        # add any missing sections
                        if s not in sections_to_process:
                            sections_to_process.append(s)
                            
            print "reduced parts_to_process=",sections_to_process            
                    
            #SCons.Script.GetOption("early_exit")
            if self.__hasStored and sections_to_process:
                
                # If we have stored data we will try to do some logic to reduce startup time
                # by doing some form of reduce reads based on what we know is up-to-date or not
                
                policy=SCons.Script.GetOption("load_logic")
                api.output.verbose_msg(['loading'],"Using load logic: {0}".format(policy))
                if policy =='case1' or glb.engine._build_mode=='clean':
                    #fully load all direct depends ( no cache loads )
                    loader=direct_depends_loader(sections_to_process,self)
                
                elif policy=='case2':
                    #Load all Part that are out of date, immediate depends from cache, ignore everything else
                    loader=section_changed_loader(sections_to_process,self)
                
                elif policy=='case3':
                    pass # fill in
                    
                elif policy =='all':
                    # load everything
                    self.__hasStored=False
                    loader=load_all_roots_loader(self)
            else:
                api.output.verbose_msg(['loading'],"Loading everything as there target is unknown")
                self.__hasStored=False
                loader=load_all_roots_loader(self)
                    
        else:
            api.output.verbose_msg(['loading'],"Loading everything as there is no cache")
            loader=load_all_roots_loader(self)
        up_to_date=loader()
                
        if up_to_date and nodes_up_to_date:
            api.output.verbose_msg(['loading'],"Everything is up-to-date!")
            api.output.print_msg("Targets are up to date!")
            glb.engine.UpToDateExit()
              
        #read_start=time.time()
        #for p in root_parts:
        #    part_file_load_time=time.time()
        #    # see if this shoudl be loaded from cache
        #    if cache and building and p.Alias not in out_date_list and p.Alias not in do_not_load and p.ForceLoad==False :
        #        cache=datacache.GetCache("part-"+p.Alias)
        #        msg="{0} is up-to-date, loaded from cache.".format(p.Alias)
        #        p._setup_from_cache_data(cache)
        #        self._load_part_from_cache(p)
        #        p._map_alias()
        #    elif p.Alias in do_not_load:
        #        msg="{0} is up-to-date, skipped loading.".format(p.Alias)
        #    else:
        #        if skip_update_check:
        #            msg="{0} loaded from file.".format(p.Alias)
        #        elif p.ForceLoad==True and p.Alias not in out_date_list:
        #            msg="{0} was force loaded from file.".format(p.Alias)
        #        else:
        #            msg="{0} is out-of-date, loaded from file.".format(p.Alias)
        #        p.ReadFile()
        #        # move this?? This maps any unknown Part() calls that should be rebound to a parts object
        #        self._clean_unknown(p)
        #    
        #        # figure out if this part is new style or old style
        #        valid_sec=self.hasValidSection(p)
        #        if not p._hasTargetFiles() and valid_sec:
        #            # new format
        #            p.Format='new'
        #            has_valid_sections=True
        #        elif p._hasTargetFiles() and valid_sec:
        #            # mixed.. not sure what to do yet with this...
        #            #print "mixed",p.Name
        #            pass
        #        elif p._hasTargetFiles() and not valid_sec:
        #            #old format
        #            # if old format we have also processed the part
        #            p.Format='classic'
        #            p._map_alias()
        #            p._setup_sdk()
        #            p._map_targets()
        #        else:
        #            # did not define anything to do?
        #            # could be a root parts with subparts?
        #            p.Format='unknown'
        #            p._map_alias()
        #            p._setup_sdk()
        #            #print "unknown",p.Name
        #    api.output.verbose_msg(['loading'],"{0:60}[{1:.2f} secs]".format(msg,(time.time()-part_file_load_time)))
        #    api.output.console_msg(" Loading %3.2f%% %s \033[K"%((cnt/total*100),msg))
        #    cnt+=1
        #
        #if has_valid_sections:
        #    # given that we have new sections to process
        #    #get targets
        #    
        #    for t in targets:
        #        t=target_type(t)
        #        # find out what section type this target wants
        #        sections=self.GetSectionsBasedOnTarget(t)
        #        #for each section that that wants to be handled this target
        #        for section_type in sections:
        #            #process that section
        #            self.ProcessSection(section_type,t)
        
        self.map_scons_target_list(up_to_date)
        glb.pnodes.clear_node_states()
        
        
    def ProcessSection(self,sec_type,target):
        ''' 
        This function will fully process a section type for a given target
        '''
        #get function to handle processing 
        func=sec_type.GetHandler()
        #call function with target to have defined for build
        func(self,target)


    def GetSectionsBasedOnTarget(self,target):
        '''
        This functions tries to map the alias to a given sections that would
        process the target correctly
        '''
        # parse the target to get any possible concepts
        if target.isPartTarget() == False:
            target.all=True
            if target.orginal_string not in ['all','.']:
                api.output.warning_msg('Target "%s" is unknown to Parts, it may be known to SCons. Force reading all data'%target.orginal_string)
        if target.concept is None: # no concept defined
            concept='build'
        else: 
            concept=target.concept
        
        # get all sections that handle the given concepts
        ret=[]
        for s in self.sections:
            if s.HandleConcept(concept):
                ret.append(s)
        return ret
    
    def hasValidSection(self,part):
        '''
        This function test to see if the Part has state the show it has a valid section defined
        '''
        return part._has_valid_sections()
        
    def UpdateOnDisk(self,part_set=None):
        ''' Update any parts that need to be updated on disk
        
        @param part_set The set of Part to see if they are up-to-date, if test all Parts
        '''
        # we need to see if any part needs to be checked out or updated
        #loop each part and ask it need to be updated
        p_list=vcs.task_master.task_master()
        s_list=vcs.task_master.task_master()
        if part_set is None:
            part_set=self.parts.values()
        for p in part_set:
            # if so add to queue for checkout
            vcsobj=p.Vcs
            if vcsobj.NeedsToUpdate():
                # we check to see if the vcs object allow for the 
                # parallel checkout policy.
                if vcsobj.AllowParallelAction():
                    p_list.append(vcsobj)
                else:
                    s_list.append(vcsobj)
        retcode=0    
        def post_vcs_func(jobs,tm):
            if jobs.were_interrupted():
                retcode=3
                api.output.error_msg("Updating of disk was interrupted!",show_stack=False)
            elif tm.Stopped:
                retcode=4
                api.output.error_msg("Errors detected while updating disk!",show_stack=False)
                    
        #checkout anything in the queue
        try:
            if p_list._has_tasks():
                # get value for level of number of concurrent checkouts
                vcs_j=SCons.Script.GetOption('vcs_jobs')
                if vcs_j == 0:
                    vcs_j=SCons.Script.GetOption('num_jobs')
                p_list.append(None)
                jobs = SCons.Job.Jobs(vcs_j, p_list)
                jobs.run(postfunc = lambda : post_vcs_func(jobs,p_list))
            if s_list._has_tasks():
                p_list.append(None)
                jobs = SCons.Job.Jobs(1, s_list)
                jobs.run(postfunc = lambda : post_vcs_func(jobs,s_list))
        except:
            glb.engine.def_env.Exit(retcode)
        finally:
            for p in part_set:
                p.Vcs.PostProcess()
            datacache.SaveCache(key='vcs')
            
        
    def _add_part(self,object):
        if object.Alias is None:
            self.__to_map_parts.append(object)
            return
        self.__part_count+=1
        object._order_value=self.__part_count
        self.parts[object.Alias]=object
        glb.pnodes.AddPNodeToKnown(object)
        
    def _clean_unknown(self,known_pobj):
        for i in self.__to_map_parts:
            if i.Name==known_pobj.Name and\
                i.Version==known_pobj.Version and\
                i._kw.get('TARGET_PLATFORM',glb.engine.def_env['TARGET_PLATFORM']) == known_pobj.Env['TARGET_PLATFORM']:                
                known_pobj._merge(i)
                self.__to_map_parts.remove(i)
                break

    def _from_alias(self,alias):
        '''
        given an alias get the defined part with this alias
        '''
        return self.parts.get(alias,None)

    def _from_env(self,env):
        '''
        given an env get the defined part with this alias
        '''
        return self._from_alias(env.get('PART_ALIAS'))
        
    
    def _has_name(self,name):
        ''' return True if we have reason to believe this is a Part name that is known
        We return True if We have a 100% match, in the known names. If this is empty
        we guess based on what in the cache
        '''
        if name in self._alias_list:
            return True
        # check the cache
        if _get_stored_root_alias(name) is not None:
            return True
        # we can't say that we know we have a Part with this name
        return False
        
    def _from_target(self,target,local_space=None,user_reduce=None):
        name=target.name
        tmp=[]
        if local_space:
            for pobj in local_space:
                # if we have a match in the local space it has to match, or fail
                if pobj.Name == name:
                    tmp.append(pobj)
        if tmp==[]:        
            alias_lst=self._alias_list(name)
            if alias_lst!=[]:
                alias_lst=[self._from_alias(i) for i in alias_lst]
        else:
            alias_lst=tmp
        
        ret=self.reduce_list_from_target(target,alias_lst)
        
        #if user_reduce:
            #user_reduce(name,ret)
        
        return ret
        
        
    def _from_nvp(self,name,ver_range,target_platform,local_space=None):
        
        ret=None
        last_ver=None
        platform=target_platform
        alias_lst=self._alias_list(name)
        
        #the Depends on logic will try to verify these object for possible
        # matches, else error. ie IF the part name matches the rest of it has to
        # dependons staements with no matching name fall trhought the "global"
        # set of Parts to match
        if local_space:
            api.verbose_msg(['part_mapping'],"Has local Space")
            for i in local_space:
                pobj=i
                # if we have a match in the local space it has to match, or fail
                if pobj.Name == name:
                    this_ver=pobj.Version
                    if this_ver in ver_range and this_ver >= last_ver and target_platform==pobj.PlatformMatch:
                        last_ver=this_ver
                        ret=pobj
                    else:
                        api.output.error_msg
                        (
                        'Part Alias "%s" does not match requirement name: "%s", version_range: "%s" platform: "%s"'%
                            (pobj.Alias,
                            name,
                            ver_range,
                            target_platform
                            )
                        )
                                
        for i in alias_lst:
            pobj=self._from_alias(i)
            if pobj is None: 
                # should not happen
                api.output.error_msg(
                    '"%s" Alias is not defined, unexcepted error.'%
                    i
                    )
            
            if pobj.Name == name:
                # get the version info
                this_ver=pobj.Version 
                if this_ver in ver_range and this_ver >= last_ver and target_platform==pobj.PlatformMatch:
                    last_ver=this_ver
                    ret=pobj
            
        return ret
    
    
    def reduce_list_from_target(self,tobj,part_lst):
        part_lst=copy.copy(part_lst)
        for k,v in tobj.properties.iteritems():
            for pobj in part_lst[:]:
                if k == 'version':
                    if common.is_string(v):
                        v=version.version_range(v+'.*')
                    if pobj.Version not in v:
                        part_lst.remove(pobj)
                elif k in ['target','target-platform','target_platform']:
                    if pobj.Env['TARGET_PLATFORM'] != v:
                        part_lst.remove(pobj)
                elif k in ['platform_match']:
                    if pobj.PlatformMatch != v:
                        part_lst.remove(pobj)
                elif k in ['cfg','config','build-config','build_config']:
                    if not pobj.Env.isConfigBasedOn(v):
                        part_lst.remove(pobj)
                elif k == 'mode':
                    mv=v.split(',')
                    for v in mv:
                        if v not in pobj._mode:
                            part_lst.remove(pobj)
                            break
                else:
                    #look up in the parts environment
                    try:
                        if common.is_list(pobj.Env[k]):
                            mv=v.split(',')
                            for v in mv:
                                if v not in pobj._mode:
                                    part_lst.remove(pobj)
                                    break
                        elif pobj.Env[k] != v:
                            part_lst.remove(pobj)
                    except KeyError:
                        part_lst.remove(pobj)
        return part_lst
                
        

    def _alias_list(self,name=None):
        '''
        given an a part name return a list of all parts alias that 
        could be matches for that name
        '''
        if name is None:
            return self.__name_to_alias
        return self.__name_to_alias.get(name,set([]))
    
    def add_name_alias(self,name,alias):
        try:
            self.__name_to_alias[name].add(alias)
        except KeyError:
            self.__name_to_alias[name]=set()
            self.__name_to_alias[name].add(alias)


    #def is_whole_part_up_to_date(self,alias):
    #    ''' 
    #    this check all the sub parts of the alias root part to see if they 
    #    are up to date
    #    '''
    #    
    #    def process_sub(sub):
    #        sub_data=datacache.GetCache("part-"+sub)
    #        if sub_data is None:            
    #            api.output.verbose_msg("update_check","%s is out of date because there no DataCache file"%sub)
    #            self.is_whole_part_up_to_date.cache[sub]=False
    #            return False
    #        
    #        if self.is_part_up_to_date(sub_data['alias']) == False:
    #            self.is_whole_part_up_to_date.cache[sub]=False
    #            return False
    #        
    #        for sub in sub_data['subparts']:
    #            if process_sub(sub) == False: return False
    #        self.is_whole_part_up_to_date.cache[sub]=True
    #        return True
    #        
    #            
    #    try:
    #        return self.is_whole_part_up_to_date.cache[alias]
    #    except AttributeError:
    #        self.is_whole_part_up_to_date.__dict__['cache']={}
    #    except KeyError:
    #        pass
    #    
    #    # see if we have data at all for this alias
    #    data=datacache.GetCache("part-"+alias)
    #    if data is None:
    #        
    #        api.output.verbose_msg("update_check","%s is out of date because there no DataCache file"%alias)
    #        self.is_whole_part_up_to_date.cache[alias]=False
    #        return False
    #    #get the root alias for this guy
    #    root_alias=data['root_alias']
    #    return process_sub(root_alias)
    #        
    #    
    #def is_part_up_to_date(self,alias,check_all=False):
    #    '''
    #    see if the alias is up to data
    #    alias - alias to the part we want to test
    #    chack_all -- default to false, will check all node, not exit at first failure
    #    this is useful for verbosing what is not up to date
    #    '''
    #    import config
    #    if check_all == False:
    #        try:
    #            return self.is_part_up_to_date.cache[alias]
    #        except AttributeError:
    #            self.is_part_up_to_date.__dict__['cache']={}
    #        except KeyError:
    #            pass
    #    data=datacache.GetCache("part-"+alias)
    #    
    #    # see if we have a cache file 
    #    had_error=False
    #    if data is None:
    #        api.output.verbose_msg("update_check","%s is out of date because there no DataCache file"%alias)
    #        if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #        return False
    #        
    #    # see if the part file is different
    #    if os.path.isfile(data['file']['name']):
    #        # it should exist
    #        if node_helpers.node_up_to_date(data['file']) == False:
    #            if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #            return False
    #    else:
    #        api.output.verbose_msg("update_check",'%s is out of date because file "%s" does not exist'%(alias,data['file']['name']))
    #
    #    # next we test the build context files
    #    
    #    for t,flist in data.get('config_context',{}).iteritems():
    #        # first check to see if this is the file would use
    #        cfg_files=config.get_defining_config_files(
    #                        data['config'],
    #                        t,
    #                        platform_info.HostSystem(),
    #                        platform_info.SystemPlatform(data['target_platform']))
    #        # check to see that we have the same amount of files
    #        #print cfg_files,flist
    #        if len(cfg_files)!=len(flist):
    #            api.output.verbose_msg("update_check",'%s is out of date because the set of files defining configuration "%s" for tool "%s" are different.'%(alias,data['config'],t))
    #            if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #            return False
    #        for f in flist:
    #            
    #            if f['name'] in cfg_files:
    #                #this file is in the set of previous found files
    #                # check if file has changed
    #                if f is not None:
    #                    if node_helpers.node_up_to_date(f) == False:
    #                        had_error=True
    #                        if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #                        if not check_all: return False        
    #            else:
    #                api.output.verbose_msg("update_check",'%s is out of date because the set of files defining configuration "%s" for tool "%s" are different.\n The file "%s" was not in set of: %s'%(alias,data['config'],t,f['name'],cfg_files))
    #                if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #                return False
    #                
    #    
    #    # next we test the build context files
    #    for t in data.get('build_context',[]):
    #        if node_helpers.node_up_to_date(t) == False:
    #            had_error=True
    #            if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #            if not check_all: return False
    #
    #    #test each node that we mapped to this Component
    #    for t in data.get('nodes',[]):                
    #        if node_helpers.node_up_to_date(t) == False:
    #            had_error=True
    #            if check_all==False: self.is_part_up_to_date.cache[alias]=False
    #            if not check_all: return False
    #            
    #    if had_error: return False
    #    if check_all==False: self.is_part_up_to_date.cache[alias]=True
    #    return True

   
        
    def Store(self,goodexit):
        if goodexit:
            stored_data=datacache.GetCache("part_map")
            data={}
            # we want to store information about the Parts we have in this run
            tmp= stored_data['known_parts'] if stored_data else {}
            has_old=False
            # this needed to tell if we have a alias target
            # however I may not need all the data that is stored
            for k,v in self.parts.iteritems():
                format=v.Format
                if format != 'new': has_old=True
                if v.isRead: # might need to relook at this case when we get new formats working
                    tmp[k]={
                        'name':v.Name,
                        #'version':v.Version,
                    
                        'format':format,
                        'root_alias':v.Root.Alias
                    }
            
            data["known_parts"]=self.parts
            
            tmp= stored_data['name_to_alias'] if stored_data else {}
            # this is needed to help with name targets
            for name,aliaslst in self.__name_to_alias.iteritems():
                tmp2={}
                for alias in aliaslst:
                    pobj=self._from_alias(alias)
                    tmp2[pobj.ID]=pobj
                tmp[name]=tmp2
            
            data['name_to_alias']=tmp
        
            # not sure about this one
            data["hasClassic"]=has_old
            datacache.StoreData("part_map",data)
            
            
    def add_stored_node_info(self,node,nlist):
        ''' this function tries to figure out if the given node depends on any parts
        If it does it add the information, if it does not it adds the node itself
        '''
        # check to see if the cache is good
        if self.__hasStored==False: return
        # get node data if any
        if node.Stored and node.Stored.components:
            # we have parts information to add
            for alias, sections in node.Stored.components.iteritems():
                for section in sections:
                    nlist.append(section)
        elif node.Stored:
            # we are here because there as no data stored about what sections to
            # load for this node. This is not an issue as this node should have been
            # define by normal means.. we only need to see what it depends on
            
            # check the state to see if we seen this node
            if getattr(node,'_node_info_checked',False):
                return 
            
            # check that we have binfo for this node
            if node.get_stored_info() is None:
                # this might be an Alias that was defined
                # we want to get any stored binfo we have and assign it
                if isinstance(node,SCons.Node.Alias.Alias):
                    binfo=glb.pnodes.GetAliasStoredInfo(node.ID)
                    if binfo:
                        # this is a little hacky... look at cleaning up..
                        class wrapper(object):
                            def __init__(self,binfo,ninfo=None):
                                self.binfo=binfo
                                self.ninfo=ninfo
                        node._memo['get_stored_info']=wrapper(binfo)
                    else:
                        self.__hasStored=False
                        return
                else:
                    self.__hasStored=False
                    return
            
            # we have binfo
            binfo=node.get_stored_info().binfo
            nodes=getattr(binfo,'bsources',[])+getattr(binfo,'bdepends',[])+getattr(binfo,'bimplicit',[])
            rlist=[]
            # for each node we dependon see if we have stored info about what sections to load
            for n in nodes:
                # get each node we care about.
                tnode=glb.pnodes.GetNode(n)
                tlist=[]
                # check the children node
                self.add_stored_node_info(tnode,tlist)
                # set the node as being checked
                tnode._node_info_checked=True
                #add any node section to the list
                common.extend_unique(nlist,tlist)    
        else:
            #there is no stored data.. cache bad or missing.
            self.__hasStored=False
        # set the node as being checked
        node._node_info_checked=True
            