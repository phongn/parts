
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
import requirement # for loaders
from target_type import target_type
import config

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

# basic loader all loader are based on
class base(object):
    
    def process_depends(self,part,depends):
        return

class load_all_roots_loader(base): #task_master type
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
        
        total = len(parts_to_load) * 1.0
        cnt=0
        # in case of a fallback we really want to make sure
        # all known parts are loaded from file. We need to set
        # that state, so any promotions forms of cache to file
        # happen correctly
        t1=time.time()
        for pobj in parts_to_load:
            #print 8769, pobj.ID, pobj.isLoading, pobj.ReadState, pobj.LoadState, pobj._remove_cache
            pobj.UpdateReadState(glb.load_file)
            pobj.isLoading=False
        for pobj in parts_to_load:
            self.pmgr.LoadPart(pobj)
            api.output.console_msg("Loading {0:.2%} \033[K".format(cnt/total,cnt,total))
            cnt+=1
        num_parts=len(self.pmgr.parts)
        tt=time.time()-t1
        if num_parts:
            api.output.verbose_msgf(['loading','load_stats'],"Loaded {0} Parts\n Total time:{1} sec\n Time per part:{2}",num_parts,tt,tt/num_parts)
        api.output.print_msg("Loaded {0} Parts".format(num_parts,))
        # we are loading everything..so we don't want to exit early
        return False
        


class direct_depends_loader(base): #task_master type
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
            if pobj.ReadState==glb.load_file:
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
            if pobj.ReadState==glb.load_file:
                self.pmgr.LoadPart(pobj)
        return False        


class no_depends_loader(base): #task_master type
    '''
    This loads all target Parts files, and assume all dependants are up to date, loading them from cache
    '''
    def __init__(self,targets,pmanager):
        # set of sections to build 
        #.. assume nodes are filtered out if ther did not expand to a section
        self.sections=targets 
        self.pmgr=pmanager
        
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
        
        pass
            
    def __call__(self): 
        
        sec_to_load=[]
        # loop for each section
        for sec in self.sections:
            # get the stored info
            stored_data=sec.Stored
            if stored_data is None:
                #return False to signal there was a cache issue
                self.hasStored=False
                
            # set read state for this section  
            sec.ReadState=glb.load_file
            if stored_data.part.Stored.parent:
                try:
                    tmp=stored_data.part.Stored.parent.Stored.sections[sec.Name]
                except KeyError:
                    tmp=stored_data.part.Stored.parent.Stored.sections['build']
                if tmp not in self.sections:
                    self.sections.append(tmp)
            if sec.Name=='utest':
                # this is a bit of a hack
                # but in general with classic formats (maybe new as well.. don't know yet)
                # we want to load the Build sections as well.
                tmp=glb.pnodes.GetPNode("build::{0}".format(stored_data.part.ID))
                tmp.ReadState=glb.load_cache
                self.sections.append(tmp)

            #for each of the dependents we need to set the depends as cache load                       
            for dep in stored_data.dependson:
                dsec=dep['Section']
                dsec.ReadState=glb.load_cache
                if dsec not in sec_to_load:                
                    sec_to_load.append(dsec)

            if sec not in sec_to_load:                
                sec_to_load.append(sec)
            
        total = len(sec_to_load) * 1.0
        cnt=0
        for sec in sec_to_load:
            if sec.ReadState == glb.load_cache:
                self.pmgr.LoadSection(sec)
                api.output.console_msg("Loading {0:.2%} ({1}/{2} sections) \033[K".format(cnt/total,cnt, total))
                cnt+=1

        for sec in sec_to_load:
            if sec.ReadState == glb.load_file:
                self.pmgr.LoadSection(sec)
                api.output.console_msg("Loading {0:.2%} ({1}/{2} sections) \033[K".format(cnt/total,cnt, total))
                cnt+=1
            
        return False       

class section_changed_loader(base): #task_master type
    '''
    figures our what we need load. basic logic is to test the dependents first
    Then the container defining that and move inwards (ie part->section->node)
    '''
    def __init__(self,targets,pmanager):
        # set of sections to build 
        #.. assume nodes are filtered out if ther did not expand to a section
        self.sections=targets 
        self._sections=[]
        self._section_info={}
        self.pmgr=pmanager
        
        # state
        self._process_depend=False
        self._up_to_date=True
        self._knowncfgs={}
        self._knownbuilders={}
        
    @property
    def hasStored(self):
        return self.pmgr.hasStored
    
    @hasStored.setter
    def hasStored(self,value):
        if value==False:
            raise errors.LoadStoredError
    
    def TagToPartLoad(self,pobj):
        '''Tag the Part and all sub parts to be loaded from file
        '''
        pobj.UpdateReadState(glb.load_file)
        if pobj.Stored: # this maybe a new previously unknown subpart
            for sub in pobj.Stored.subparts:
                tmp=glb.pnodes.GetPNode(sub)
                self.TagToPartLoad(glb.pnodes.GetPNode(sub))
           
             
    def LoadSection(self,sec):
        ''' Set the state of this section depends to cache, and the given section to load
        
        Note this is focused currently for "classic" format logic. This mean that we could have a 
        build and maybe utest section defined. Given this we need to set the build section case 
        when the section is not of type build. This is because the classic formats does not allow 
        the needed seperation of read and processing that the new format allows for.
        '''
        
        # check to see if this is a utest section type, if so we will want to
        # do this again for the "build" section of the same part.
        
        if sec.Name =='utest':
            self.LoadSection(sec.Stored.part.Stored.sections['build'])
        
        sec.ReadState=glb.load_file
        self._up_to_date=False
        #tag dependents that are not in ignore state to a cache state
        for dep in sec.Stored.dependson:
            tsec=dep['Section']
            if tsec.ReadState == glb.load_none:
                # set the cache state
                tsec.ReadState=glb.load_cache
                
        #if this sec part is not a root we need to tag the parents depends as cache
        while sec.Stored.part.Stored.parent:
            try:
                sec=sec.Stored.part.Stored.parent.Stored.sections[sec.Name]
            except KeyError:
                sec=sec.Stored.part.Stored.parent.Stored.sections['build']
            for dep in sec.Stored.dependson:
                tsec=dep['Section']
                tsec.ReadState=glb.load_cache
        
                
            
    def process_depends(self,pobj,depends):
        if self._process_depend:
            # we want to try to map the dependancy to get a set of possible parts 
            # we need to look at. If the matching value Parts files are out of date
            # we want to load them now as well
            for dep in depends:
                # get all reasonable matches 
                # might have more than on at this point as we don't have some environment data
                # to help with matching.. in these cases we just add all possible cases to be safe
                new_sections=dep.StoredMatchingSections
                api.output.verbose_msgf("process_depends","{0} mapped to {1}",dep.PartRef.Target,new_sections)
                for dep_sec in new_sections:   
                    # Check to see if this has been loaded already.
                    # if so skip 
                    if dep_sec.LoadState == glb.load_file:
                        api.output.verbose_msgf("process_depends","{0} already loaded",dep_sec.ID)
                        continue
                    # Check to see if this item is has the same root parts
                    if dep_sec.Stored and dep_sec.Stored.part.Stored.root != pobj.Root:
                        # if this is so we want to load it from cache at the very least
                        dep_sec.ReadState=glb.load_cache
                        same_root_part=False
                    else:
                        same_root_part=True
                    #retest that the parts file has changed and or context is different
                    self.CheckForContextChanged(dep_sec,recursive_call=True)
                    # We don't have and stored state for some reason
                    # or we have a force_load state set on this item
                    # so we load it.
                    if dep_sec.Stored is None or dep_sec.Stored.part.Stored.force_load ==True:
                        self.LoadSection(dep_sec)
                    api.output.verbose_msgf("process_depends","{0} LoadState={1} ReadState={2}",dep_sec.ID,dep_sec.LoadState, dep_sec.ReadState)
                    # check to see that item is not already read in
                    # and that it not part of this current Part we are currently loading
                    if dep_sec.LoadState < dep_sec.ReadState and not same_root_part:
                        # need to change the cwd directory in the node FS object
                        # get the current location    
                        tmp=glb.engine.def_env.fs.getcwd()
                        # change the root location
                        glb.engine.def_env.fs.chdir(glb.engine.def_env.Dir("#./"),True)
                        # do load
                        self.pmgr.LoadSection(dep_sec)
                        # change back to previous location
                        try:
                            # change variant and and system
                            glb.engine.def_env.fs.chdir(tmp,True)
                        except OSError:
                            # change src
                            glb.engine.def_env.fs.chdir(tmp.srcdir,True)
                            # then variant ( which out changing system)
                            glb.engine.def_env.fs.chdir(tmp,False)

    # need to refactor this function
    def CheckForContextChanged(self,sec,req=None,recursive_call=False):
        '''tests if the parts file, build and config context for the section as changed'''
        
        try:
            # we try to see if we know of this already
            # given that we do we want to see if this has changed
            if self._section_info[sec.ID]['changed'] is not None:
                # since this has changed we already know we will load everything 
                return True
            elif self._section_info[sec.ID]['requirements']:
                # This is not changed so we need to add any special requirements we
                # might have, or set this to None to load everything or this is a top level
                # call meaning that all requirements need to be tested as this was part of the targets
                # add new requirements
                if req is None or not recursive_call: # if this is None and we already have a setup
                    # this means we need build everything this component has
                    self._section_info[sec.ID]['requirements']=None
                else:
                    self._section_info[sec.ID]['requirements'] |= req
                return False
                
        except KeyError:
            context_changed=False

            if sec._remove_cache:
                return True
        
            stored_data=sec.Stored
            # test that we have Stored data
            if stored_data is None:
                raise errors.LoadStoredError

            self._section_info[sec.ID]={
                    'section':sec
                    }
            ## given the file did not change .. check the config context
            if self.hasConfigContextChange(sec):
                self._section_info[sec.ID]['changed']='config'
                self.LoadSection(sec)
                self._up_to_date=False
                context_changed=True
            # given the file did not change .. check the builder context
            elif self.hasBuildContextChanged(sec):
                self._section_info[sec.ID]['changed']='builder'
                self.LoadSection(sec)
                self._up_to_date=False
                context_changed=True

            # see if the Parts file defining the sections is changed
            changed=False
            if sec.hasPartFileChanged() or sec.Stored.part.Stored.root.Mode != sec.Stored.part.Stored.root.Stored.mode:
                # in this case we are going to be out of date
                # however we need to check the "new" dependance for being out of date
                # as these may add new files to load in some way
            
                #load this file ...
                api.output.verbose_msgf("update_check",'{0} is out of date because the part file has changed.',sec.ID)
                #sec.ReadState=glb.load_file
                self.TagToPartLoad(sec.Stored.part.Stored.root)
                self._up_to_date=False
                self.pmgr.LoadSection(sec)
                
                # we remap the dependance based on hyrid Dependon logic
                # updated and Stored information to find the correct mapping
                changed=True
                for dep in sec.Depends:
                    new_depend_list=[]
                    #get the all possible matches that could match within reason
                    new_sections=dep.StoredMatchingSections
                    for dep_sec in new_sections:
                        new_depend_list.append({
                        'Section':dep_sec
                        })
                        if sec.LoadState != glb.load_file: 
                            # If this is loaded.. it may not have a cache for use to check
                            # beside checking the cache is pointless, as it fully loaded
                            self.CheckForContextChanged(dep_sec,dep.Requires,recursive_call=True)
                    sec.Stored.dependson=new_depend_list
            else:
                # this file has not changed so we can use the current Stored information    
                for dep in stored_data.dependson:
                    #get the Section
                    dep_sec=dep['Section']
                    if req == None:
                        dep_req=dep['Requires']
                    else:
                        # Only pass requirements if we depend on them as well
                        dep_req=requirement.REQ()
                        tmp=dep['Requires']
                        for r in req:
                            if r in tmp:
                                dep_req|=r
                    
                    sec_changed=self.CheckForContextChanged(dep_sec,dep_req,recursive_call=True)
                    if sec_changed:
                        api.output.verbose_msgf("update_check",'{0} out-of-date! Dependent section "{1}" is out of date',sec.ID,dep_sec.ID)
                        self.LoadSection(sec) # set the state
                        #self.pmgr.LoadSection(sec) # do the load
                        changed=True
        
            # add to list of all section to process
            self._sections.append(sec)
            
            if changed:    
                # add that this section is out of date
                self._section_info[sec.ID]['changed']="file"
                self._section_info[sec.ID]['requirements']=requirement.REQ()                
                return True
            else:
                self._section_info[sec.ID]['changed']=None
                self._section_info[sec.ID]['requirements']=req         
            
            return context_changed
           
    def hasConfigContextChange(self,sec):
        
        ## test the files that define the configuration contexts
        # call method to get stored info.. also get info from "part" object is needed
        stored_cfg_data=sec.Stored.GetConfigContext()
        key=str(stored_cfg_data)
        try:
            return self._knowncfgs[key]
        except KeyError:
            # next we test the build context files
            for tool,file_list in stored_cfg_data.iteritems():
                # get the files we would use in this run for a given tool
                cfg_files=config.get_defining_config_files(
                                sec.Stored.part.Stored.config,
                                tool,
                                platform_info.HostSystem(),
                                sec.Stored.part.Stored.target_platform)
                ## first check to see if these are the files we have cached
                # check to see that we have the same amount of files
                if len(cfg_files)!=len(file_list):
                    api.output.verbose_msgf(
                    "update_check",
                    '{0} is out of date because the set of files defining configuration "{1}" for tool "{2}" are different.',
                    sec.ID,sec.Stored.part.Stored.config,tool
                    )
                    self._knowncfgs[key]=True
                    return True
                # test each file
                for file in file_list:    
                    if file['name'] in cfg_files:
                        #this file is in the set of previous found files
                        # check if file has changed
                        if not node_helpers.node_up_to_date(file):
                            api.output.verbose_msgf("update_check",'{0} is out of data because the file "{1}" that defines the configuration has changed',sec.ID,file['name'])
                            self._knowncfgs[key]=True
                            return True
                    else:
                        api.output.verbose_msgf(
                        "update_check",
                        '{0} is out of date because the set of files defining configuration "{1}" for tool "{2}" are different.\n The file "{3}" was not in set of: {4}',
                         sec.ID,sec.Stored.part.Stored.config,tool,file['name'],cfg_files
                                
                            )
                        self._knowncfgs[key]=True
                        return True
        self._knowncfgs[key]=False
        return False
                                
    def hasBuildContextChanged(self,sec):
        
        ## test the files that define the builders 
        # call method to get stored info.. also get info from "part" object is needed
        stored_bld_data=sec.Stored.GetBuilderContext()
        key=str(stored_bld_data)
        
        
        for bld in stored_bld_data:
            try:
                #Do we know of this item yet
                tmp=self._knownbuilders[bld['name']]                
                # yes we do
                if tmp: # is it out of date?
                    api.output.verbose_msgf(
                      "update_check",
                      '{0} is out of date because file "{1}" that defines builders has changed',
                            sec.ID,bld['name']
                    )
                    return tmp
            except KeyError:    
                # we don't know of this file as of yet
                # next we test the build context file to see if this is good or bad
                if node_helpers.node_up_to_date(bld) == False:
                    api.output.verbose_msgf(
                        "update_check",
                        '{0} is out of date because file "{1}" that defines builders has changed',
                         sec.ID,bld['name']
                    )
                    self._knownbuilders[bld['name']]=True
                    return True
                self._knownbuilders[key]=False
        # if we got here we loop through all builder items
        # and it all looks good, return there false to say no changes
        return False
                
                
    def CheckForNodeExportChanges(self,sec):
        
        if self._section_info[sec.ID]['changed']:
            return 
        
        stored_data=sec.Stored

        # check to see if the dependent is changed for some reason, then check to see
        # check to see if the stuff it depends in the dependent Export tables have changed
        for dep in stored_data.dependson:
            dep_sec=dep['Section']
            # see if the dependent has changed
            if self._section_info[dep_sec.ID]['changed'] is not None:
                self._section_info[sec.ID]['changed']='dependent'
                api.output.verbose_msgf("update_check",'{0} out-of-date! Dependent section "{1}" is out of date',sec.ID,dep_sec.ID)
                self.LoadSection(sec)
                return
            # see if the esig changed from what we required of it
            reqs=dep['Requires']
            rsigs=dep['rsigs']
            
            # see if our view of the Part we dependon changed:
            # this is a test of the dependentsection content csig. 
            # This value will change if data the dependent csig 
                        
            # we test each requirment signiture (rsig) we have and see if that data 
            # in export data signiture (esig) has changed from our last run
                        
            for req in reqs:
                if dep_sec.Stored.esigs.get(req.key,'0')!=rsigs.get(req.key,'0'):
                    #print dep_sec.Stored.esigs.get(req.key,'0'),rsigs.get(req.key,'0')
                    self._section_info[sec.ID]['changed']='export'
                    api.output.verbose_msgf("update_check",'{0} out-of-date! Dependent values "{1}" from "{2}" changed',sec.ID,req.key,dep_sec.ID)
                    self.LoadSection(sec)
                    return
        
    def CheckForNodeRequirementsChanges(self,sec):
        
        if self._section_info[sec.ID]['changed']:
            return 
        
        stored_data=sec.Stored
        # Are requirement we have for this Section changed?
        # the requirements should be all the requirements by all Part that depend on this section
        target_nodes=[]
        requirements=self._section_info[sec.ID]['requirements']
        
        if requirements:
            # there are requirements we want to check for.. 
            # here we turn each requirement in to a Node
            # which we will use, via the node logic to see if it changed or out of date.
            for r in requirements:
                if r.key in stored_data.exported_requirements:
                    target_nodes.append(glb.pnodes.GetNode('{0}::alias::{1}::{2}'.format(stored_data.name,stored_data.part.ID,r.key)))          
        else:    
            # if this was None used the default requirement
            # this is actually the general node to build this the whole section
            # which is what we want here.
            target_nodes=[glb.pnodes.GetNode('{0}::alias::{1}'.format(stored_data.name,stored_data.part.ID))]
        
        for tnode in target_nodes:
            # None node are not found as a export of this part.. 
            # we can ignore it because it was not an value the given section defined
            # if this was an error we could not have saved the data
                
            # the hasNodeChanged uses logic added to the SCons Nodes to see if the value it changed by looking at what it 
            # depends on and if it view of the dependent is different
            api.output.verbose_msgf("update_check_extra",'{0} checking for changes in node {0}',sec.ID,tnode.ID)
            if tnode and not tnode.pisUpToDate: #hasNodeChanged
                    # we are out of date
        
                    self._section_info[sec.ID]['changed']="nodes"
                    api.output.verbose_msgf("update_check",'{0} out-of-date! Section Target "{1}" is out of date',sec.ID,tnode),
                    self.LoadSection(sec)
                    break
                

    def CheckForDependentSectionChanges(self,sec):
        
        if self._section_info[sec.ID]['changed']:
            return 
        
        stored_data=sec.Stored
        # this checks to see if the section has a "AlwaysBuild" state that was found
        if sec.AlwaysBuild:
            self._section_info[sec.ID]['changed']='always_build'
            api.output.verbose_msgf("update_check",'{0} out-of-date! section contains node that called AlwaysBuild()',sec.ID)
            self.LoadSection(sec)
            return

        # check to see if the dependent is changed for some reason, then check to see
        # check to see if the stuff it depends in the dependent Export tables have changed
        for dep in stored_data.dependson:
            dep_sec=dep['Section']
            # see if the dependent has changed
            if self._section_info[dep_sec.ID]['changed'] is not None:
                self._section_info[sec.ID]['changed']='dependent'
                api.output.verbose_msgf("update_check",'{0} out-of-date! Dependent section "{1}" is out of date',sec.ID,dep_sec.ID)
                self.LoadSection(sec)
                return
            
            

    def CheckTargets(self):

        # need to do a little refactoring.

        #get the set of new unknown root parts that have been added.
        # we want to load these, so we can have the information added to the DB cache
        # and to prevent issues with mapping if an existing Parts depends on the new value
        
        new_parts=self.pmgr.GetNewParts()
        # we could try to delay load these "unknowns" if we have a unknown mapping issue.
        # might look at that when I refactor the load logic cases.
        # for now just load these, as this should not be common
        for pobj in new_parts:
            api.output.verbose_msgf("update_check",'Part "{0}" is new, forcing load',pobj.ID)
            self.pmgr.LoadPart(pobj)

        #given the sections we need to two tree runs
        #1) run is to see what has context changes (file, builder and config files changes)
        #2) see what targets/source file and exported items are different
        
                
        # see if the Part file changed..is so load it and figure out new depends the best we can
        # see if the builder config context changed
        # at the end of this we will have a list of sections in the order to load, a dictionary of 
        # sectionID:{
        #   section -- the section for quick look up
        #   changed -- tell us that the state of the section being changed
        #   requirements -- we need to have each section test for being up to date
        #}
        # NOTE! changes == None ( no change ), file, config, build, nodes, exports,dependent 
        # (at this point None,file,config,build,dependent should be seen)
        st=time.time()
        self._process_depend=True
        total=len(self.sections)*1.0
        cnt=0
        for sec in self.sections:
            api.output.console_msg("Checking Parts File for Changes {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
            if sec.Stored is None:
                raise errors.LoadStoredError
            #check to see if the file even exists ( might have been removed)
            elif not os.path.exists(sec.Stored.part.Stored.file['name']):
                #most likely this part does not exists anymore.. ie was removed
                # load the whole Part
                self.TagToPartLoad(sec.Stored.part.Stored.root)
                #set this section to be removed
                sec._remove_cache=True
                sec.Stored.part._remove_cache=True
                api.output.verbose_msgf("update_check",'{0} does not seem to exist any more, reloading Part {1}',sec.ID,sec.Stored.part.Stored.root.ID)
            elif sec.hasPartFileChanged() or sec.Stored.part.Stored.root.Mode != sec.Stored.part.Stored.root.Stored.mode:
                self.TagToPartLoad(sec.Stored.part.Stored.root)
            cnt+=1
        api.output.console_msg("Checking Parts File for Changes {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))

        cnt=0
        for sec in self.sections:
            api.output.console_msg("Checking Content {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
            # this is a hack we should refactor out..
            # set load state of soem code in the parts manager
            # happen to set the read state
            if sec.ReadState == glb.load_file:
                self.LoadSection(sec)
            self.CheckForContextChanged(sec)
            cnt+=1
        self._process_depend=False
        api.output.console_msg("Checking Content {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
        #print 1,time.time()-st
        
                
        # we go through the list again and if the state of the section is None
        # we test:
        # 1) that the direct dependents are not out of date
        # 2) the exports of those dependents have not changed
        # 3) the requirements for this section are up-to-date
        # Note we have to do this again as a file might have change causing a upper section
        # of stuff to be forced loaded.. 
        st=time.time()
        total=len(self._sections)*1.0
        cnt=0
        for i in self._sections:
            api.output.console_msg("Checking Export Data {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
            self.CheckForNodeExportChanges(i)
            cnt+=1
        #print 2,time.time()-st
        api.output.console_msg("Checking Export Data {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
        
        # this pass we are going to test the nodes to be out of data
        st=time.time()
        total=len(self._sections)*1.0
        cnt=0
        for i in self._sections:
            api.output.console_msg("Checking Node State {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
            self.CheckForNodeRequirementsChanges(i)
            cnt+=1
        api.output.console_msg("Checking Node State {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
        #print 3,time.time()-st
        
        # there is still a chance that a node changed that is a side effect is found out of date,
        # but the section that depend on the given section with the side effect did not get 
        # tagged as out of date.
        st=time.time()
        total=len(self._sections)*1.0
        cnt=0
        for i in self._sections:
            api.output.console_msg("Checking Dependents {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
            self.CheckForDependentSectionChanges(i)
            cnt+=1
        api.output.console_msg("Checking Dependents {0:.2%} {1}/{2} \033[K".format((cnt/total),cnt,total))
        #print 4,time.time()-st
        
        # at this point we should be good. We want to sort the items to dependent items ideally get loaded first
        # however we only really need to sort/group the sections by there root part, as the loading of this item 
        # should force the rest of the sub-parts to load
        #root_parts_to_load=[]
        #for sec in self._sections:
            #print sec.Stored.part.Stored.root
            #if sec.Stored.part.Stored.root not in root_parts_to_load:
                #root_parts_to_load.append(sec.Stored.part.Stored.root)
        
        self._sections.sort(scmp)
        
        # at this point the list of parts with the correct load state set.
        # we go through this list and load anything that needs to be loaded
        #for sec in self._sections:
            #stored_data=sec.Stored
            #print sec.ID ,"depends on:"
            #for dep in stored_data.dependson:
            #    dep_sec=dep['Section']
            #    print "  ",dep_sec.ID
        
        # we are done
        return 
                                    
    def __call__(self): 
        
        # Do update checks
        self.CheckTargets()
        #print "total Node",glb.pnodes.TotalNode()
        # load anything is it is out of date
        if not self._up_to_date:
            total = len(self._sections) * 1.0
            cnt=0
            for s in self._sections:
                #print s.ID,s.ReadState
                api.output.console_msg("Loading {0:.2%} ({1}/{2} sections) \033[K".format(cnt/total,cnt,total))
                self.pmgr.LoadSection(s)
                cnt+=1
                
        
        return self._up_to_date
  
    
class part_manager(object):
    
    def __init__(self):
        self.sections=glb.sections
        self.parts={} # a dictionary of all parts objects by there alias value
        self.__name_to_alias={} #a dictionary of a known Parts name and possible alias that match
        self.__to_map_parts=[] # stuff that needs to be mapped, else it is wasted space
        self.__hasStored= SCons.Script.GetOption("parts_cache") # used to help prevent wasting time on cases of incomplete cache data
        self.__part_count=0 # number of parts we have defined.. 
        self.__root_part_count=0 # number of Major parts/components we have defined.. 
        self.__loader=None
        glb.engine.CacheDataEvent+=self.Store
        self.__new_parts=set()
    
    @property
    def Loader(self):
        return self.__loader
    
    def map_targets_stored_pnodes(self,targets):
        '''Turn the targets into a list of pnodes or Node ( given if can't be mapped to a Pnode) objects'''
        ret=[] # the new target list
        ret_nodes=[]
        
        
        stored_data=datacache.GetCache("part_map")
        
        if stored_data is None:
            self.__hasStored=False
            api.output.verbose_msg(['target_mapping'],"part_map data cache did not load, Loading everything")
            return
        stored_name_to_alias=stored_data['name_to_alias']
            
        for t in SCons.Script.BUILD_TARGETS:
            name_matches=None
            if isinstance(t,SCons.Node.Node):
                api.output.verbose_msg(['target_mapping'],"Target is SCons node")
                tmp=[]
                self.add_stored_node_info(t,tmp)
                ret+=tmp
                ret_nodes.append((t,tmp))
                if not self.__hasStored: 
                    api.output.verbose_msgf(['target_mapping'],'No Stored info found for "{0}", Loading everything',t.ID)
                    return
            else:
                #This is a string to a target we need to figure out
                tobj=target_type(t)
                # first see if this is ambiguous
                # ie this is something like 'foo'
                # we don't know if this is a name::foo, alias::foo or a directory called foo, etc
                if tobj.isAmbiguous:
                    # we want to figure out based on stored information is this something we should know about
                    known_parts=stored_data['known_parts']
                    ta=target_type("alias::"+str(t))
                    tn=target_type("name::"+str(t))
                    
                    # this might be a name
                    name_matches=stored_name_to_alias.get(tobj.Name)
                    #try:
                    #    for k,pobj in stored_name_to_alias[tn.Name].iteritems():
                    #        try:
                    #            name_matches[pobj.Stored.root.ID].add(pobj)
                    #        except KeyError:
                    #            name_matches[pobj.Stored.root.ID]=set([pobj]) 
                    #except KeyError:
                    #    pass
                    if name_matches:
                        # we have some matches
                        api.output.verbose_msgf(['target_mapping'],'Target: "{0}" is a known name',tn.Name)
                        tobj=tn
                    #see if this is an alias we have
                    elif glb.pnodes.isKnownPNode(ta.Alias):# known_parts.keys():
                        # this looks like an alias we should know about
                        api.output.verbose_msgf(['target_mapping'],'Target: "{0}" is a known alias',t)
                        tobj=ta
                    elif glb.pnodes.isKnownNodeStored(t):
                        node=glb.pnodes.GetNode(t)
                        tmp=[]
                        self.add_stored_node_info(node,tmp)
                        ret+=tmp
                        ret_nodes.append((node,tmp))
                        if not self.__hasStored: 
                            api.output.verbose_msgf(['target_mapping'],'Target: "{0}" missing stored data, Loading everything',t)
                            return
                        api.output.verbose_msgf(['target_mapping'],'Target: "{0}" is a known SCons node',t)
                        continue
                    else:
                        # we don't know this.. assume we have to load everything
                        api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a not known, Loading everything')
                        return None
                
                #process the target node into Alias nodes                
                if tobj.Concept:
                    concept=tobj.Concept
                else:
                    concept='build'
                    tobj.Concept=concept                       
                if tobj.hasAlias:
                    # add the concept::alias section
                    # we make an alias node as this works best for
                    # all cases with groups or recursion
                    if glb.pnodes.isKnownPNodeStored(str(tobj)): 
                        
                        node=glb.pnodes.GetNode(str(tobj))
                        tmp=[]
                        self.add_stored_node_info(node,tmp)
                        ret+=tmp
                        if not self.__hasStored: 
                            api.output.verbose_msgf(['target_mapping'],'Target: "{0}" missing stored data, Loading everything',tobj)
                            return
                        api.output.verbose_msgf(['target_mapping'],'Target: "{0}" is a Alias',tobj)
                    
                    ## get pobj                    
                    #if glb.pnodes.isKnownPNodeStored(tobj.Alias): 
                    #    pobj=glb.pnodes.GetPNode(tobj.Alias)
                    #    # get stored section
                    #    tmp=pobj.Stored.sections[tobj.Section]
                    #    api.output.verbose_msg(['target_mapping'],'Target: "{0}" is a Alias'.format(tobj))
                    #    ret.append(tmp)
                    else:
                        # this is not known.. backout
                        api.output.verbose_msgf(['target_mapping'],'No stored information found for "{0}", Loading everything',tobj)
                        return None
                elif tobj.Name:
                    api.output.verbose_msgf(['target_mapping'],'Target: "{0}" is a name',tobj)
                    if name_matches is None:
                        name_matches=stored_name_to_alias.get(tobj.Name)
                                                
                    if not name_matches:
                        api.output.verbose_msgf(['target_mapping'],'No matches found for name, Loading everything',tobj)
                        return None # we don't have any known found values.. backout
                    
                    pobjs_lst = name_matches.values()
                    # try to process known values
                    ## keep in mind this assume classic formats
                    ## and it will get stuff wrong.. 
                    ## what it can get wrong is loading stuff we might not build
                    ## and even possiblity not loading stuff ( ie in more complex cases of sub-parts with lots of Customization )
                    ## however common simple cases should be ok ( ie no sub-parts or no to minimum Customization form the default settings)
                    ## ideally setup with only new formats will not have these issues, as we can read first, and get need info
                    name_matches=self.reduce_list_from_target_stored(tobj,set(pobjs_lst))
                    def _map_alias(_pobj,_tobj):
                        # the section does not match the concept we want to use the Alias form to get the "sections"
                        # as this does an extra check for some cases in which the Alias maps to nodes that require
                        # special logic to happen, such as AlwaysBuild()
                        tstr="{0}::alias::{1}{2}".format(_tobj.Concept,_pobj.Alias,"::" if tobj.isRecursive else "")
                        node=glb.pnodes.GetNode(tstr)
                        if node:
                            self.add_stored_node_info(node,[])
                        else:
                            self.__hasStored=False
                        if not self.__hasStored: 
                            api.output.verbose_msgf(['target_mapping'],'Target: "{0}" missing stored data, Loading everything',tstr)
                            return True
                        return False

                    def get_subpart_section(_pobj):
                        for subpobj in _pobj.Stored.subparts:
                            subpobj=glb.pnodes.GetPNode(subpobj)
                            if tobj.Section != tobj.Concept:
                                if _map_alias(subpobj,tobj):
                                    return
                            tmp=subpobj.Stored.sections.get(tobj.Section)
                            if tmp:
                                ret.append(tmp)
                            get_subpart_section(subpobj)

                    if not name_matches:
                        api.output.verbose_msgf(['target_mapping'],'No matched found for "{0}", Loading everything',tobj)
                        return None

                    for pobj in name_matches:
                        # the target mapping logic will handle the case of groups mapping
                        # for loading a section a group still requires us to load a whole section
                        # get stored section
                        if tobj.isRecursive:
                            # try to load this section
                            if tobj.Section != tobj.Concept:
                                if _map_alias(pobj,tobj):
                                    return
                            tmp=pobj.Stored.sections.get(tobj.Section)
                            if tmp:
                                ret.append(tmp)
                            # if we are recursive, we need to add all section from any subpart we can find.
                            get_subpart_section(pobj)
                                
                        else:
                            if tobj.Section != tobj.Concept:
                                if _map_alias(pobj,tobj):
                                    return
                                
                            # try to load this section
                            tmp=pobj.Stored.sections.get(tobj.Section)
                            # did we find a section.. if not error and exist
                            if tmp is None:
                                api.output.verbose_msg(['warning','target_mapping'],'Part {0} does not define a {1} section'.format(pobj.Stored.name, tobj.Section))
                                #api.output.error_msg('Part {0} does not define a {1} section'.format(pobj.Stored.name, tobj.Section))
                            else:
                                ret.append(tmp)
                        
                else:
                    # add the concept:: alias as we define this
                    tmp=glb.engine.def_env.Alias(concept+"::")[0]
                    api.output.verbose_msgf(['target_mapping'],'Target: "{0}" is a concept',tobj)
                    self.add_stored_node_info(tmp,ret)
                    if not self.__hasStored: 
                        api.output.verbose_msgf(['target_mapping'],'No stored information found for "{0}", Loading everything',tobj)
                        return
        
        return (ret,ret_nodes)
        
    def LoadSection(self,sec):
        
        # when we load a section we in a way load the part that defines the section
        # there are a few different cases that can happen
        # 1) the section is ignored ( we don't care about it), but the Part needs to be loaded from file or cache
        # 2) the section is to load from cache, but the Part needs to be loaded from file
        # 3) the section and part have same load requirements
        # in general as we don't have "new formats" yet the section and parts are always 3)
        # the part can never be lower than the sections read state, the Parts is always
        # equal or higher
        pobj=sec.Stored.part
        
        if sec._remove_cache:
            api.output.verbose_msgf(['loading'],"{0} being ignored as it seems to not exist in the SConstruct anymore",pobj.ID)

        if (sec.LoadState < glb.load_file and sec.ReadState == glb.load_file):
            self.LoadPart(pobj)
            if pobj._remove_cache:
                sec._remove_cache=True
            else:
                sec.LoadState = glb.load_file # should be set.. just being safe
        elif (sec.LoadState < glb.load_cache and sec.ReadState == glb.load_cache):
            self.LoadPart(pobj) # load part from cache (function will do nothing if already loaded)
            if pobj._remove_cache:
                sec._remove_cache=True
            elif sec.LoadState < glb.load_cache: 
                sec.LoadFromCache() # load section from cache   
                sec.LoadState = glb.load_cache     
        
    def LoadPart(self,pobj):
        part_file_load_time=time.time()
        processed=False
        #see if this part is setup
        if pobj._remove_cache:
            api.output.verbose_msgf(['loading'],"{0} being ignored as it seems to not exist in the SConstruct anymore",pobj.ID) 
        elif pobj.isSetup:
            # it is setup, so the parent has been read in
            if pobj.isLoading:
                api.output.verbose_msgf(['loading'],"{0} is already being loaded. Not Loading!",pobj.ID)
                return
            elif pobj.LoadState == glb.load_file:
                api.output.verbose_msgf(['loading'],"{0} was already loaded. Ignoring!",pobj.ID)
                return
            elif (pobj.LoadState < glb.load_file and pobj.ReadState == glb.load_file) or\
                 not glb.pnodes.isKnownPNodeStored(pobj.ID) or\
                 self.__hasStored==False or\
                 pobj.ForceLoad:
                # we want to read this Parts file. However this might be getting promoted form being loaded from cache to file 
                # in this case we need to check that the parent has been read in if this is a subpart. If this is not the
                # case we want to read it in first and return. The reading of the parent should cause the sub-part to be
                # read, when the sub parts Part() call happens. This is mainly a "classic" format issue. The new format
                # should not have this problem.
                if not pobj.isRoot and pobj.Parent.LoadState < glb.load_file and not pobj.Parent.isLoading:
                    api.output.verbose_msgf(['loading'],"Trying to loading from file: {0},\n but the parent Part has not been read yet",pobj.ID)
                    self.LoadPart(pobj.Parent)
                    return
                     
                #read in the data fully
                api.output.verbose_msgf(['loading'],"Loading from file: {0}",pobj.ID)
                pobj.isLoading=True
                pobj.UpdateReadState(glb.load_file)
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
                    #print "mixed",pbj.Name
                    pass
                elif pobj._hasTargetFiles() and not valid_sec:
                    #old format
                    # if old format we have also processed the part
                    pobj.Format='classic'
                    pobj._map_alias()
                    pobj._setup_sdk()
                    pobj._map_targets()
                    #print "unknown",pobj.Name
                else:
                    # did not define anything to do?
                    # could be a root parts with subparts?
                    pobj.Format='unknown'
                    pobj._map_alias()
                    pobj._setup_sdk()
                    pobj._map_targets()
                    #print "unknown",pobj.Name
            #api.output.verbose_msg(['loading'],"{0:60}[{1:.2f} secs]".format(msg,(time.time()-part_file_load_time)))
            #api.output.console_msg(" Loading %3.2f%% %s \033[K"%((cnt/total*100),msg))
            #cnt+=1
                pobj.LoadState = glb.load_file
                processed=True
                pobj.isLoading=False
                
            elif pobj.LoadState < glb.load_cache and pobj.ReadState == glb.load_cache: #not pobj.isRead and pobj.ReadState == glb.load_cache:
                api.output.verbose_msgf(['loading'],"Loading from cache: {0}",pobj.ID)
                pobj.isLoading=True
                pobj.LoadFromCache()
                self._add_part(pobj) 
                pobj.LoadState = glb.load_cache
                pobj.isLoading=False
                processed=True
                
            elif pobj.ReadState == glb.load_none:
                api.output.verbose_msgf(['loading'],"not loading: {0}",pobj.ID)
        else:
            # we are trying to load some sub-part that has not had it parent read in yet
            # there are two cases for this parent.. 
            # 1)it will be read-in via load_cache 
            # 2)it will be read in via load_file.
            # If the Parts parents is loaded yet, we need to load it
            policy=SCons.Script.GetOption("load_logic")
            if pobj.Stored.parent is None:
                # this part was probally removed
                api.output.verbose_msgf(['loading'],"not loading: {0} because it looks like it is not defined anymore",pobj.ID)
                self.__hasStored=False
                pobj._remove_cache=True
                
                if policy!='all':
                    api.output.verbose_msgf(['loading'],"Trying to set load-logic to all logic",pobj.ID)
                    SCons.Script.Main.OptionsParser.values.load_logic='all'
                    #SCons.Script.SetOption("load_logic",'all')
                    raise errors.LoadStoredError
                return
            if pobj.Stored.parent.LoadState < pobj.Stored.parent.ReadState: 
                try:
                    self.LoadPart(pobj.Stored.parent)
                except errors.LoadStoredError:
                    raise
            # check to see if the whole parts seems to be missing
            if pobj.Stored.parent._remove_cache:
                pobj._remove_cache=True
                api.output.verbose_msgf(['loading'],"{0} being ignored as {1} seems to not exist in the SConstruct anymore",pobj.ID,pobj.Stored.root.ID) 
                return
                
            #Given that it is read at this point. we need to check to see if we are read
            # given that parent should have loaded.. we should be loaded as well
            # if we are not and we are to be read in as cache ( what we should see if not read-in yet)
            # we want to load this part from cache
            
            # At this point we should be setup at the very least, if not loaded
            # if the parent was loaded from cache we might not be loaded yet
            if pobj.LoadState < glb.load_cache and pobj.ReadState == glb.load_cache:
                api.output.verbose_msgf(['loading'],"Loading From cache: {0}",pobj.ID)
                pobj.LoadFromCache()
                self._add_part(pobj) 
                pobj.LoadState = glb.load_cache
                processed=True
            # it is possible a loader gave us a part we want to ignore    
            elif pobj.ReadState == glb.load_none:
                api.output.verbose_msgf(['loading'],"not loading: {0}",pobj.ID)
            elif pobj.LoadState == glb.load_none:
                # if we get here the most likely case is this is a complex part with lots of subparts
                # check to see if the parent still defined this sub-part, it may have been removed or renamed
                if pobj.ID in pobj.Stored.parent.Stored.subparts and not pobj.Stored.parent.isLoading:
                    #This appears to be so. We want to mark this data to be removed so we don't look for it again
                    api.output.verbose_msgf(['loading'],"Can't load {0} as this is a subpart does not appear to exist in the parent anymore.",pobj.ID)
                    pobj._remove_cache=True
                
                elif pobj.Stored.parent.isLoading:
                    # we most likely have a case in which a sub-part that has yet to be read in is being force read
                    # as it is in a depends of a sub-part that was defined before it in the Parts file
                    # there is nothing we can do with this given the classic format. so we punt and hope for the best
                    if policy!='all':
                        api.output.verbose_msgf(['loading'],"Trying to set load-logic to all logic",pobj.ID)
                        SCons.Script.Main.OptionsParser.values.load_logic='all'
                        self.__hasStored=False
                        #SCons.Script.SetOption("load_logic",'all')
                        raise errors.LoadStoredError
                    else:
                        api.output.verbose_msgf(['loading'],"Can't load {0} as parent part is still loading. Skipping, May cause failures",pobj.ID)
                
                else:
                    
                    if policy!='all':
                        api.output.verbose_msgf(['loading'],"Can't load {0} Not sure why? Falling back",pobj.ID)
                        api.output.verbose_msgf(['loading'],"Trying to set load-logic to all logic",pobj.ID)
                        SCons.Script.Main.OptionsParser.values.load_logic='all'
                        self.__hasStored=False
                        #SCons.Script.SetOption("load_logic",'all')
                        raise errors.LoadStoredError
                    else:
                        api.output.verbose_msgf(['loading'],"Can't load {0} Not sure why? Skipping, May cause failures",pobj.ID)
                return
                
        if processed:
            api.output.verbose_msgf(['loading'],"Loaded {0:45}[{1:.2f} secs]",pobj.ID,(time.time()-part_file_load_time))
                 
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

        # store setup state if this is a read cache or ignore case, as it might need to load latter as a file
        # and we will not be able to get the orginal state to "reinit" this component
        if tmp.ReadState != glb.load_file:
            tmp_args=new_kw
            tmp_args.update({
                            'alias':alias,
                            'file':parts_file,
                            'mode':mode,
                            'vcs_t':vcs_type,
                            'default':default,
                            'append':new_append,
                            'prepend':new_prepend,
                            'create_sdk':create_sdk,
                            'package_group':package_group,
                            'parent_part':parent_part
                           })
            tmp._cache["init_state"]=tmp_args

        if tmp.LoadState == glb.load_cache:
            #If this is the case we need to make sure the sections are processed
            for s in tmp.Stored.sections.itervalues():
                if s.ReadState == glb.load_cache:
                    s.LoadFromCache() # load section from cache   
                    s.LoadState = glb.load_cache     
        
        return tmp
    
    def map_scons_target_list(self,uptodate):
        ''' here we try to map the Parts target values to values SCons can build'''

        stored_data=datacache.GetCache("part_map")
        # trying to translate based on everything being read in
        new_list=[] # the new target list
        skip_list=[]
        def _add_list(_nodestr,orginal_str):
            '''
            This is a helper funtions to test if the node is known and or possibly valid
            before we try to add the node to the target list
            '''
            
            if glb.pnodes.isKnownNodeStored(_nodestr):
                #This is known value
                if not glb.pnodes.isKnownNode(_nodestr):
                    # but it is not defined. we assume this is because the load logic did 
                    # not load it because it was up-to-date
                    api.output.verbose_msgf(['loading'],'Skipping target "{0}" as it is believe to have been skipped by the load logic manager',orginal_str)
                    skip_list.append(orginal_str)
                    return

            elif not glb.pnodes.isKnownNode(_nodestr):
                # This is not defined or known in the cache
                # since it is not defined or known to be a valid target we error
                api.output.error_msgf("{0} is an invalid target",orginal_str,show_stack=False)

            new_list.append(_nodestr)

        api.output.verbose_msgf(['loading'],"Orginal BUILD_TARGETS: {0}",SCons.Script.BUILD_TARGETS)
        for t in SCons.Script.BUILD_TARGETS:
            tobj=target_type(t)
            # first see if this is ambiguous
            if tobj.isAmbiguous:
                # we are not sure
                # first we try to see if the name can be matched
                ta=target_type("alias::"+str(t))
                tn=target_type("name::"+str(t))
                if self.__name_to_alias.get(tn.Name):
                    #we are sure this is a Parts value
                    tobj=tn
                # see if this is an alias value
                elif self.parts.get(ta.Alias):
                    #we are sure this is a Parts value
                    tobj=ta
                else:
                    #we are sure this is a SCons value
                    new_list.append(t)
                    continue            
            
            #we are that this is a Part target format
            # see what concept is defined
            if tobj.Concept:
                concept=tobj.Concept
            else:
                concept='build'
            if tobj.Alias:
                # add the concept::alias alias as we define this
                basestr="{0}::alias::{1}".format(concept,tobj.Alias)
                if tobj.hasGroups:
                    for grp in tobj.Groups:
                        basestr="{0}::{1}".format(basestr,grp)
                        if tobj.isRecursive:
                            basestr="{0}::".format(basestr)
                        _add_list(basestr,t)
                else:
                    if tobj.isRecursive:
                        basestr="{0}::".format(basestr)
                    _add_list(basestr,t)
                
            elif tobj.Name:
                #This case can have multipul matches
                # get a list of known alias that have this name
                alias_lst=self.__name_to_alias.get(tobj.Name)
                
                if alias_lst is None:
                    # we might have a case in which this item is not loaded
                    # we need to check that we have a cache and that this item 
                    # defined here. Given that we trust that it safe to ignore
                    if stored_data is not None and\
                       stored_data['name_to_alias'].get(tobj.Name,None) is not None:
                        # If this is true we can say we know that we tried to load this part
                        # but it was probally skipped by the load logic for some reason
                        # and we should ignore it
                        api.output.verbose_msgf(['loading'],'Skipping target "{0}" as it is believe to have been skipped by the load logic manager',t)
                        skip_list.append(t)
                        continue
                    #error we don't have a target called this to build
                    api.output.error_msg("Unknown name: %s"%(tobj.Name),show_stack=False)
                else:
                    pobj_lst = [self._from_alias(i) for i in alias_lst]
                #filter out any of these that don't match the properties
                pobj_lst=self.reduce_list_from_target(tobj,set(pobj_lst))
                if not pobj_lst:
                    api.output.error_msg('"%s" did not map to any defined Parts'%t)
                for pobj in pobj_lst:
                    basestr="{0}::alias::{1}".format(concept,pobj.Alias)
                    if tobj.hasGroups:
                        for grp in tobj.Groups:
                            basestr="{0}::{1}".format(basestr,grp)
                            if tobj.isRecursive:
                                basestr="{0}::".format(basestr)
                            _add_list(basestr,t)
                    else:
                        if tobj.isRecursive:
                            basestr="{0}::".format(basestr)
                        _add_list(basestr,t)
            else:
                # add the concept:: alias as we define this
                basestr="{0}::".format(concept)
                if tobj.hasGroups:
                    
                    # fix up later.. till then error if this case is used
                    api.output.error_msg('Target case of <concept>::::<group> is not supported yet!')
                    # we have groups so we need to get all the 
                    # sections that mapped to this
                    
                    # for each part with this section we test to see if it has this group
                    for pobj in self.parts.itervalues():
                        if pobj.hasSection(tobj.Section):
                            pobj.Section(tobj.Section).groups
                    # if it does add it to the build list, else skip it
                    
                    
                    for grp in tobj.Groups:
                        basestr="{0}::{1}".format(basestr,grp)
                        if tobj.isRecursive:
                            basestr="{0}::".format(basestr)
                        _add_list(basestr,t)
                else:
                    _add_list(basestr,t)
        SCons.Script.BUILD_TARGETS=new_list
        if skip_list:
            api.output.verbose_msgf(['loading'],"Targets we skipped: {0}",skip_list)
        api.output.verbose_msgf(['loading'],"Updated BUILD_TARGETS: {0}",SCons.Script.BUILD_TARGETS)
        
    def ProcessParts(self):
        ''' 
        This function will process all the Parts object based on the targets
        '''
        
        #######    
        ##update the disk
        ##is everything up to date on disk update file on disk?
        ## if not we need to update it
        if SCons.Script.GetOption('update'):
            api.output.print_msg("Updating disk")
            self.UpdateOnDisk( self.parts.values() )
            api.output.print_msg("Updating disk - Done")

        if len(SCons.Script.BUILD_TARGETS) == 1 and SCons.Script.BUILD_TARGETS[0] == "extract_sources":
            return
        
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
            try:
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
                                s.ReadState=glb.load_file
                                # add any missing sections
                                if s not in sections_to_process:
                                    sections_to_process.append(s)
            except errors.LoadStoredError:
                self.__hasStored=False                
            api.output.verbose_msg(['loading'], "reduced sections to process=",[i.ID for i in sections_to_process])
                    
            #SCons.Script.GetOption("early_exit")
            if self.__hasStored and sections_to_process:
                
                # If we have stored data we will try to do some logic to reduce startup time
                # by doing some form of reduce reads based on what we know is up-to-date or not
                
                policy=SCons.Script.GetOption("load_logic")
                if policy=='default': 
                    policy='min'
                if SCons.Script.GetOption("interactive") and policy != "unsafe":
                    policy='all'
                api.output.verbose_msgf(['loading'],"Using load logic: {0}",policy)
                if policy =='target' or glb.engine._build_mode=='clean':
                    #fully load all direct depends ( no cache loads )
                    loader=direct_depends_loader(sections_to_process,self)
                
                elif policy=='min':
                    #Load all Part that are out of date, immediate depends from cache, ignore everything else
                    loader=section_changed_loader(sections_to_process,self)
                
                elif policy=='unsafe':
                    # load only the sections assume everything is up to date
                    loader=no_depends_loader(sections_to_process,self)
                    api.output.warning_msg('''Load logic case of "unsafe" is being used!
 All dependents are assumed up-to-date!
 If this is not the case the build may be incorrect or fail!''',show_stack=False)
                    
                    
                elif policy =='all':
                    # load everything
                    self.__hasStored=False
                    loader=load_all_roots_loader(self)
            else:
                api.output.verbose_msg(['loading'],"Loading everything as the given targets are unknown")
                self.__hasStored=False
                loader=load_all_roots_loader(self)
                    
        else:
            api.output.verbose_msg(['loading'],"Loading everything as there is no cache")
            self.__hasStored=False
            loader=load_all_roots_loader(self)
        
        self.__loader=loader
        try:
            up_to_date=self.__loader()
        except errors.LoadStoredError:
            api.output.verbose_msg(['loading'],"Loading everything as changes seem to be complex")
            self.__hasStored=False
            self.__loader=load_all_roots_loader(self)
            up_to_date=self.__loader()
                
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
        
        def post_vcs_func(jobs,tm):
            if jobs.were_interrupted():
                tm.ReturnCode=3
                api.output.error_msg("Updating of disk was interrupted!",show_stack=False)
            elif tm.Stopped:
                tm.ReturnCode=4
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
            if p_list.ReturnCode:
                glb.engine.def_env.Exit(p_list.ReturnCode)
            if s_list.ReturnCode:
                glb.engine.def_env.Exit(p_list.ReturnCode)
            glb.engine.def_env.Exit(2)
        finally:
            for p in part_set:
                p.Vcs.PostProcess()
            datacache.SaveCache(key='vcs')
            
        
    def _add_part(self,object):
        if object.Alias is None:
            self.__to_map_parts.append(object)
            return
        self.__part_count+=1 
        if object.Root._order_value ==0:
            if object.isRoot:
                self.__root_part_count+=1
                object._order_value=self.__root_part_count
            else:
                object._order_value=object.Root._order_value
        
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
        
    def _from_target(self,target,local_space=None,user_reduce=None,use_stored_info=False):
        
        name=target.Name
        tmp=set()
        full_set=set()
        if local_space:
            for pobj in local_space:
                # if we have a match in the local space it has to match, or fail
                if pobj.Name == name:
                    tmp.add(pobj)
                    
        # if we found something in the local space tmp will have data in it                    
        if not tmp: 
            if use_stored_info:
                # what we had stored
                if name:
                    if datacache.GetCache("part_map") is None:
                        return []
                    stored_dict=datacache.GetCache("part_map")['name_to_alias'].get(name)
                    if stored_dict:
                        for v in stored_dict.itervalues():
                            full_set.add(v)
                elif target.Alias and self.parts.get(target.Alias):
                    full_set.add(self.parts.get(target.Alias))
                else:
                    return []
                    #api.output.error_msg("{0} target is to ambigous to find any possible match".format(target.OrignialString))
            else:            
                # what is up-to-date
                alias_lst=self._alias_list(name)
                if alias_lst!=[]:
                    for v in alias_lst:
                        full_set.add(self._from_alias(v))
                
        else:
            full_set=tmp
        if use_stored_info:
            # need a copy for the stored case as we might want to return all possible matches
            full_set_copy=full_set.copy()
        ret= self.reduce_list_from_target_stored(target,full_set) if use_stored_info else self.reduce_list_from_target(target,full_set) 
        #if user_reduce:
            #user_reduce(name,ret)
        if use_stored_info and ret == set([]):
            return full_set_copy
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
    
    
    def reduce_list_from_target_stored(self,tobj,part_lst):
        
        api.output.verbose_msgf("stored_reduce_target_mapping","Reducing list of parts based on target {0}\n list={1}",tobj,part_lst)
        for k,v in tobj.Properties.iteritems():
            for pobj in part_lst.copy():
                api.output.verbose_msgf("stored_reduce_target_mapping"," Testing Part {0}",pobj.ID)
                if pobj.Stored is None:
                    #We have no stored info. skip test 
                    #(ie load it as it might be needed)
                    pass
                elif k == 'version':
                    api.output.verbose_msgf("stored_reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2}",k,v,pobj.Stored.version)
                    if common.is_string(v):
                        v=version.version_range(v+'.*')
                    if pobj.Stored.version not in v:
                        api.output.verbose_msgf("stored_reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['target','target-platform','target_platform']:
                    api.output.verbose_msgf("stored_reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2}",k,v,pobj.Stored.target_platform)
                    if pobj.Stored.target_platform != v:
                        api.output.verbose_msgf("stored_reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['platform_match']:
                    api.output.verbose_msgf("stored_reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2} Types:{3} {4}",k,v,pobj.Stored.platform_match,type(v),type(pobj.Stored.platform_match))
                    if pobj.Stored.platform_match != v:
                        api.output.verbose_msgf("stored_reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['cfg','config','build-config','build_config']:
                    # weak... make better code for this case
                    api.output.verbose_msgf("stored_reduce_target_mapping","  Matching Attibute: {0} Values:{1}",k,v)
                    if not pobj.Stored.config != v:# pobj.Env.isConfigBasedOn(v):
                        api.output.verbose_msgf("stored_reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k == 'mode':
                    mv=v.split(',')
                    for v in mv:
                        if v not in pobj.Stored.mode:
                            api.output.verbose_msgf("stored_reduce_target_mapping","  Removing Part {0}",pobj.ID)
                            part_lst.remove(pobj)
                            break
                else:
                    #look up in the parts environment
                    # skip this test for stored information
                    # as we don't have an env object yet
                    pass
        api.output.verbose_msgf("stored_reduce_target_mapping","Final reduced list {0}",part_lst)
        return part_lst
    
    def reduce_list_from_target(self,tobj,part_lst):
        
        api.output.verbose_msgf("reduce_target_mapping","Reducing list of parts based on target {0}",tobj)
        for k,v in tobj.Properties.iteritems():    
            for pobj in part_lst.copy():
                api.output.verbose_msgf("reduce_target_mapping"," Testing Part {0}",pobj.ID)
                if k == 'version':
                    api.output.verbose_msgf("reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2}",k,v,pobj.Version)
                    if common.is_string(v):
                        v=version.version_range(v+'.*')
                    if pobj.Version not in v:
                        api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['target','target-platform','target_platform']:
                    api.output.verbose_msgf("reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2}",k,v,pobj.Env['TARGET_PLATFORM'])
                    if pobj.Env['TARGET_PLATFORM'] != v:
                        api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}".format(pobj.ID))
                        part_lst.remove(pobj)
                elif k in ['platform_match']:
                    api.output.verbose_msgf("reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2} Types:{3} {4}",k,v,pobj.PlatformMatch,type(v),type(pobj.PlatformMatch))
                    if pobj.PlatformMatch != v:
                        api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k in ['cfg','config','build-config','build_config']:
                    api.output.verbose_msgf("reduce_target_mapping","  Matching Attibute: {0} Values:{1}",k,v)
                    if not pobj.Env.isConfigBasedOn(v):
                        api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
                elif k == 'mode':
                    mv=v.split(',')
                    api.output.verbose_msgf("reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2}",k,v,pobj._mode)
                    for v in mv:
                        if v not in pobj._mode:
                            api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                            part_lst.remove(pobj)
                            break
                else:
                    #look up in the parts environment
                    try:
                        api.output.verbose_msgf("reduce_target_mapping","  Matching Attibute: {0} Values:{1} {2}",k,v,pobj.Env[k])
                        if common.is_list(pobj.Env[k]):
                            mv=v.split(',')
                            for v in mv:
                                if v not in pobj.Env[k]:
                                    api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                                    part_lst.remove(pobj)
                                    break
                        elif pobj.Env[k] != v:
                            part_lst.remove(pobj)
                            api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                    except KeyError:
                        api.output.verbose_msgf("reduce_target_mapping","  Removing Part {0}",pobj.ID)
                        part_lst.remove(pobj)
        api.output.verbose_msgf("reduce_target_mapping","Final reduced list {0}",part_lst)
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
        
    def Store(self,goodexit):
        if goodexit:
            stored_data=datacache.GetCache("part_map")
            data={'__version__':'1.0'}
            # we want to store information about the Parts we have in this run
            # or update any parts that are read in
            tmp= stored_data['known_parts'] if stored_data else {}
            has_old=False
            # this needed to tell if we have a alias target
            # however I may not need all the data that is stored here
            # we can clean this up later
            for k,v in self.parts.iteritems():
                format=v.Format
                if format != 'new': has_old=True
                # update only part that have been loaded from file
                if v.LoadState == glb.load_file: # might need to relook at this case when we get new formats working
                    tmp[k]={
                        'name':v.Name,
                        #'version':v.Version,
                    
                        'format':format,
                        'root_alias':v.Root.Alias
                    }
            
            data["known_parts"]=tmp
            
            tmp= stored_data['name_to_alias'] if stored_data else {}
            # this is needed to help with name targets
            for name,aliaslst in self.__name_to_alias.iteritems():
                tmp2=tmp.get(name,{}) if self.__hasStored else {}
                for alias in aliaslst:
                    pobj=self._from_alias(alias)
                    tmp2[pobj.ID]=pobj
                tmp[name]=tmp2
            data['name_to_alias']=tmp
        
            # not sure about this one
            data["hasClassic"]=has_old
            datacache.StoreData("part_map",data)

            ## for each known part get the file mapped to it
            #for pobj in self.parts.iteritems():
            #    
            ## for each part file we get an MD5
            #    data[pobj.File.srcnode().path]={}
            #    fdata['csig']=pobj.File.get_csig()
            ## get the known alias and names mapped to the given part ( ie can have more of one for each)
            #    [
            #     {'alias':pobj.Alias,
            #      'names':pobj.Name,
            #        'ver':pobj.Version
            #        }
            #     ]
            #     

            
            
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
                    if node.Stored.always_build:
                        section.AlwaysBuild=True
                    if section is None:
                        self.__hasStored=False
                    else:
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
                if tnode is None:
                    self.__hasStored=False
                    return
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

    def GetNewParts(self):
        '''
        Returns a set of "new" Parts that are not known based on stored data from last run
        '''

        if self.__new_parts:
            return self.__new_parts
        
        stored_data=datacache.GetCache("part_map")
        #get stored data on known Parts
        known_parts=stored_data['known_parts']
        print known_parts
        # look to see if any parts we currently know about is not in the list.
        for pobj in self.parts.itervalues():
            if pobj.ID not in known_parts:
                self.__new_parts.add(pobj)

        return self.__new_parts



