import common
import parts
import reporter
import datacache
import node_helpers
import platform_info
import vcs
import version
from target_type import target_type


import SCons.Script
import time
import os

import SCons.Job

def pcmp(x,y):
            
    #if x.Alias == y.Alias: return 0
    xcache=datacache.GetCache("part-"+x.Alias)
    ycache=datacache.GetCache("part-"+y.Alias)
            
    if ycache:
        # Y uses X
        xiny = x.Alias in ycache['full_root_depends'] or y._uses_part(x)
        ylen = len(ycache['full_root_depends'])
    else:
        xiny=y._uses_part(x)
        ylen = len(y._uses)
    if xcache:
        # X uses Y
        yinx = y.Alias in xcache['full_root_depends'] or x._uses_part(y)
        xlen = len(xcache['full_root_depends'])
    else:
        yinx= x._uses_part(y)
        xlen = len(x._uses)
            
    if xiny: return -1
    elif yinx: return 1
    # sort my length of some sort of dependance lenght
    elif xlen > ylen: return 1
    elif xlen < ylen: return -1
    return cmp(x._order_value,y._order_value)
    
class part_manager(object):
    
    def __init__(self):
        self.sections=common.g_sections
        self.parts={} # a dictionary of all parts objects by there alias value
        self.__name_to_alias={} #a dictionary of a known Parts name and possible alias that match
        self.__to_map_parts=[] # stuff that needs to be mapped, else it is wasted space
        self.__cache_bad=not SCons.Script.GetOption("parts_cache") # used to help prevent wasting time on cases of incomplete cache data
        self.__part_count=0 # number of parts we have defined.. 
    
    def _map_target(self):
        '''
        This function maps the string targets to a a Parts Target_type to allow for better processing
        '''
        targets=SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp=target_type(t)
            
        # trying to translate based on everything being read in
        for t in targets:
            tmp=target_type(t)
            # first see if this is ambiguous
            if not tmp.isPartAlias:
                # we are not sure
                if self._alias_list.get(tmp.orginal_string) is not None:
                    #we are sure this is a Parts value
                    tmp.name=tmp.orginal_string
                else:
                    #we are sure this is a SCons value
                    has_scons_value=True
                    ret.append(tmp.orginal_string)
            
            #we are that this is a Part target format
            # see what concept is defined
            if tmp.concept:
                concept=tmp.concept
            else:
                concept='build'
            if tmp.all:
                # add the concept:: alias as we define this
                ret.append(concept)
            elif tmp.alias:
                # add the concept::alias alias as we define this
                ret.append(concept+"::alias::"+tmp.alias)
            elif tmp.name:
                #This case can have multipul matches
                # get a list of known alias that have this name
                alias_lst=self._alias_list.get(name)
                if alias_lst is None:
                    #error we don't have a target called this to build
                    print "unknown target defined!"
                #filter out any of these that don't match the properties
                for k,v in tmp.properties.items():
                    for i in alias_lst[:]:
                        pobj= self._from_alias(i)
                        if k == 'version':
                            if pobj.Version not in version.version_range(v+'.*'):
                                alias_lst.remove(i)
                        elif k in ['target','target-platform','target_platform']:
                            if pobj.Env['TARGET_PLATFORM'] != v:
                                alias_lst.remove(i)
                        elif k in ['cfg','config','build-config','build_config']:
                            if not pobj.Env.isConfigBasedOn(v):
                                alias_lst.remove(i)
                        elif k == mode:
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
                for i in alias_lst:
                    ret.append(concept+"::alias::"+i)
                                    
                                    
                    
         # trying to translate based on the cache
        for t in targets:
            tmp=target_type(t)
            # first see if this is ambiguous
            if not tmp.isPartAlias:
                # we are not sure
                if self._alias_list.get(tmp.orginal_string) is not None:
                    #we are sure this is a Parts value
                    tmp.name=tmp.orginal_string
                else:
                    #we are sure this is a SCons value
                    has_scons_value=True
                    ret.append(tmp.orginal_string)
            
            #we are that this is a Part target format
            # see what concept is defined
            if tmp.concept:
                concept=tmp.concept
            else:
                concept='build'
            if tmp.all:
                # add the concept:: alias as we define this
                ret.append(concept)
            elif tmp.alias:
                # add the concept::alias alias as we define this
                ret.append(concept+"::alias::"+tmp.alias)
            elif tmp.name:
                #This case can have multipule matches
                # get a list of known alias that have this name
                get_cached_alias_with_name
    
    def _get_stored_root_alias_from_target(self,tobj):
        ''' 
        try to get the get the root alias based on a target_type object
        '''            
        
        # first see if this is ambiguous
        if not tobj.isPartAlias:
            # we are not sure
            # first we try to see if the name can be matched
            tmp=self._get_stored_root_alias_from_name(tobj.orginal_string)
            if tmp:
                #we are sure this is a Parts value
                return tmp
            # see if this is an alias value
            tmp=self._get_stored_root_alias_from_alias(tobj.orginal_string)
            if tmp:
                #we are sure this is a Parts value
                return tmp
            else:
                #we are sure this is a SCons value
                return None
               
        if tobj.all:
            # concept:: was defined.. load everything ( clean up to be smarter)
            return []
        elif tobj.alias:
            # we have an alias.. find all root parts with this alias
            if self._get_stored_root_alias_from_alias(tobj.alias) == []:
                reporter.report_error("Unknown alias: %s"%(tobj.alias),show_stack=False)
            return self._get_stored_root_alias_from_alias(tobj.alias)
        elif tobj.name:
            #this is a name, get all root parts with this name
            if self._get_stored_root_alias_from_name(tobj.name) == []:
                reporter.report_error("Unknown name: %s"%(tobj.name),show_stack=False)
            return self._get_stored_root_alias_from_name(tobj.name)
        
        
    def _get_stored_root_alias_from_name(self,name):
        #load the global data
        tmp=datacache.GetCache("global_data")
        if tmp is None: return None
        # get the known parts list
        known_alias=tmp.get('known_parts')
        if known_alias is None: return None
        ret=[]
        # for each known part we load it cache
        # and see if it knows about the alias
        # as we can have more than one match
        for i in known_alias:
            # load cache for part
            tmp=datacache.GetCache("part-"+i)
            
            # check that there is cache data
            if tmp is None:
                # if this happens.. something is very wrong.
                # we assume all data is bad
                self.__cache_bad=True
                return None
            # see if alias is in the known set here
            
            elif tmp['name']==name:
                # if it is we have a match
                # store the root alias for this part
                common.append_unique(ret,tmp.get('root_alias'))
        else:
            return ret
        return None
    
    def _get_stored_root_alias_from_alias(self,target_str):
        '''
        Given the target_str and based on stored data what is the root part alias 
        for this part.
        '''
        #load the global data
        tmp=datacache.GetCache("global_data")
        if tmp is None: return None
        # get the known parts list
        known_alias=tmp.get('known_parts')
        if known_alias is None: return None
        ret=[]
        # for each known part we load it cache
        # and see if it knows about the alias
        # as we can have more than one match
        for i in known_alias:
            # load cache for part
            tmp=datacache.GetCache("part-"+i)
            
            # check that there is cache data
            if tmp is None:
                # if this happens.. something is very wrong.
                # we assume all data is bad
                self.__cache_bad=True
                return None
            # see if alias is in the known set here
            elif target_str == tmp['alias']:
                # if it is we have a match
                # store the root alias for this part
                common.append_unique(ret,tmp.get('root_alias'))
        else:
            return ret
        return None
    
    def _get_stored_full_root_depends(self,root_alias):
        '''
        we want the root part depends for root parts and all it subparts
        
        '''
        data=datacache.GetCache("part-"+root_alias)
        if data is None:
            print "NOT FOUND part-"+root_alias
            # in case this is not found
            return []
        return data.get('full_root_depends',[])
        
    def _is_part_file_modifed(self,pobj,data=None):
        if data is None:
            data=datacache.GetCache("part-"+pobj.Alias)
        # see if we have a cache file 
        
        if data is None:
            return False
                
        # see if the part file is different
        if pobj._file==data['file']['name']:
            # it should exist
            if os.stat(s['file']['name'])[stat.ST_MTIME] != s['file']['timestamp']:
                # time stamp is different .. check csig to be sure
                if self.def_env.File(s['file']['name']).get_csig() != s['file']['csig']:
                    return False
        else:
            return True
        return False
    
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
            package_group=parent_part._package_group
        if mode==[]:
            mode=parent_part._mode
        new_kw.update(kw)
        if 'parent_part' in new_kw:
            del new_kw['parent_part']
        new_append.update(append)
        new_prepend.update(prepend)
        
        tmp= parts.Part_t(alias=alias,file=parts_file,mode=mode,vcs_t=vcs_type,
                        default=default,append=new_append,prepend=new_prepend,
                        create_sdk=create_sdk,package_group=package_group,
                        parent_part=parent_part,**new_kw)
        # setup new object
        tmp._setup_()
        # add to set of known parts
        self._add_part(tmp)   
        #read in the data
        #print " Processing",tmp.Alias
        tmp.ReadFile()
        self._clean_unknown(tmp)
        #map the aliases
        tmp._map_alias()
        tmp._setup_sdk()
        tmp._map_targets()
                
        
        
        return tmp
    
    def _load_part_from_cache(self,pobj):
        cache=datacache.GetCache("part-"+pobj.Alias)
        for s in cache['subparts']:
                subcache=datacache.GetCache("part-"+s)
                tmp=parts.Part_t(
                        alias=subcache['short_alias'],
                        # note we want the parent src_dir as this path is based on that
                        file=common.relpath(subcache['file']['name'],cache['src_path']),
                        mode=subcache['mode'],
                        package_group=subcache['package_group'],
                        parent_part=pobj
                        )
                tmp._setup_()
                tmp._setup_from_cache_data(subcache)
                self._add_part(tmp)
                self._load_part_from_cache(tmp)
                tmp._map_alias()
                
    def _map_targets_to_root_parts(self):
        ''' This function will try to map the targets to a set of known Parts.
        If the cache is bad, or there is one target that we can't map we will
        then load everything
        '''
        root_parts=[]
        for t in SCons.Script.BUILD_TARGETS:
            tmp=self._get_stored_root_alias_from_target(target_type(t))
            
            if tmp is None:
                # we have a unknown target
                # note we could test all parts files to see if they changed
                # this would allow us to know if target could be cached safely
                root_parts=None
                break
            else:            
                #for each root alias we have we want to add the set of root parts
                # this this part and any sub parts it might have
                for t in tmp:
                    common.extend_unique(root_parts,[t]+self._get_stored_full_root_depends(t))
        if root_parts is None:
            # map everything
            return (self.parts.values(),True)
        if root_parts == []:  
            # map everything
            return (self.parts.values(),False)
        else:
            return ([self.parts[i] for i in root_parts],False)
    
    def map_scons_target_list(self):
        ''' here we try to map the Parts target values to values SCons can build'''
        # trying to translate based on everything being read in
        new_list=[] # the new target list
        reporter.verbose_msg(['loading'],"Orginal BUILD_TARGETS: %s"%SCons.Script.BUILD_TARGETS)
        for t in SCons.Script.BUILD_TARGETS:
            tobj=target_type(t)
            # first see if this is ambiguous
            if not tobj.isPartAlias:
                # we are not sure
                # first we try to see if the name can be matched
                ta=target_type("alias::"+t)
                tn=target_type("name::"+t)
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
                    reporter.report_error("Unknown name: %s"%(tobj.name),show_stack=False)
                #filter out any of these that don't match the properties
                for k,v in tobj.properties.items():
                    for i in alias_lst.copy():
                        pobj= self._from_alias(i)
                        print k,v
                        if k == 'version':
                            if pobj.Version not in version.version_range(v+'.*'):
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
                    reporter.report_error('"%s" did not map to any defined Parts'%t)
                for i in alias_lst:
                    new_list.append(concept+"::alias::"+i)
        SCons.Script.BUILD_TARGETS=new_list
        reporter.verbose_msg(['loading'],"Updated BUILD_TARGETS: %s"%SCons.Script.BUILD_TARGETS)
    
    def _make_out_of_date_list(self,root_parts):
        ''' this function takes a list of Parts and returns a list of what is considered out of date
        
        @param root_parts The lists of Parts objects to test
        
        returns a list of Parts Aliases for each parts that is out of date and a list of Parts to not even load from cache
        '''
        # if we are not building (ie reporting help or cleaning) and the cache is not good
        # we don't want to do this check
        out_of_date=[]
        do_not_load=[]
        if self.__cache_bad==False and common.g_engine._build_mode=='build':
            uttt=time.time() # the start time of the checking
            
            # see if we should do any checks at all for making a lesser set
            if SCons.Script.GetOption("incremental_cache"):
                #select some type of fast incremental logic
                if SCons.Script.GetOption("incremental_dependent_checks"):
                    # Check that dependents are up-to-date as well
                    out_of_date=self._setup_fast_incremental(root_parts)
                else:
                    # assume dependents are up to date.. may result in build issues
                    out_of_date=self._setup_fast_incremental_no_update_check(root_parts)
                    
            # otherwise we see if anything is out of date so we might be able to exit early
            elif SCons.Script.GetOption("early_exit"):
                out_of_date=self._setup_out_of_date(root_parts)
            reporter.verbose_msg("update_check_time","Total Time for update check: %s seconds"%(time.time()-uttt))
        return out_of_date, do_not_load
    
    def ProcessParts(self):
        ''' 
        This function will process all the Parts object based on the targets
        '''
        
        has_valid_sections=False
        targets=SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets == []:
            return 
        # try to map the target to a known Part, or load everything
        reporter.print_msg("Processing Targets to find known reduce set of Parts objects to define")
        root_parts,skip_update_check=self._map_targets_to_root_parts()
        
        reporter.verbose_msg(['loading'],common.DelayVariable(lambda :"Root Parts to Load : %s" %([i.Alias for i in root_parts])))
            
        #is everything up to date on disk update file on disk?
        # if not we need to update it
        reporter.print_msg("Updating disk")
        self.UpdateOnDisk( root_parts )
        
        # update check.. here we will:
        # 1) try order the parts a little based on known depends ordering
        # 2) try to figure out if everything is not up-to-date what can be loaded from the cache
        # 3) try to see if we can exit early if everything is up-to-date
        
        ##########################################
        # we sort the set of parts we plan to load
        reporter.print_msg("Sorting Targets")
        root_parts.sort(pcmp)
                
        reporter.verbose_msg(['loading'],common.DelayVariable(lambda :"Sorted : {0}".format([i.Alias for i in root_parts]) ))
        
        out_date_list=[]
        do_not_load=[]
        building=common.g_engine._build_mode=='build'                
        
        if skip_update_check==False:
            
            ##########################################################
            # here we try to figure out what is out of data if anything
            out_date_list,do_not_load=self._make_out_of_date_list(root_parts)
        
            ##########################################################
            # Here we check that state of what is out of date to see if we can exit early
            if out_date_list == [] and self.__cache_bad==False and SCons.Script.GetOption("early_exit") and building:
                reporter.print_msg("Everything seem to be up-to-date. Shutting down...")
                common.g_engine.def_env.Exit(0)
        else:
            reporter.print_msg("Skipping update checks because of unknown build targets.")
        
        # here we load all the Parts we think we should load
        reporter.print_msg("Loading Part files...")
        
        total=len(root_parts)*1.0
        cnt=1
        cache=self.__cache_bad==False and skip_update_check==False
        
        read_start=time.time()
        for p in root_parts:
            part_file_load_time=time.time()
            # see if this shoudl be loaded from cache
            if cache and building and p.Alias not in out_date_list and p.Alias not in do_not_load :
                cache=datacache.GetCache("part-"+p.Alias)
                msg="up-to-date! Loaded from cache: %s."%p.Alias
                p._setup_from_cache_data(cache)
                self._load_part_from_cache(p)
                p._map_alias()
            elif p.Alias in do_not_load:
                msg="up-to-date! Skipped loading Parts: %s."%p.Alias
            else:
                if skip_update_check:
                    msg="Loaded from file: %s."%p.Alias
                else:
                    msg="out-of-date! Loaded from file: %s."%p.Alias
                p.ReadFile()
                # move this?? This maps any unknown Part() calls that should be rebound to a parts object
                self._clean_unknown(p)
            
                # figure out if this part is new style or old style
                valid_sec=self.hasValidSection(p)
                if not p._hasTargetFiles() and valid_sec:
                    # new format
                    p._set_part_format('new')
                    has_valid_sections=True
                elif p._hasTargetFiles() and valid_sec:
                    # mixed.. not sure what to do yet with this...
                    #print "mixed",p.Name
                    pass
                elif p._hasTargetFiles() and not valid_sec:
                    #old format
                    # if old format we have also processed the part
                    p._set_part_format('classic')
                    p._map_alias()
                    p._setup_sdk()
                    p._map_targets()
                else:
                    # did not define anything to do?
                    # could be a root parts with subparts?
                    p._set_part_format('unknown')
                    p._map_alias()
                    p._setup_sdk()
                    #print "unknown",p.Name
            reporter.verbose_msg(['loading'],"{0:60}[{1:.2f} secs]".format(msg,(time.time()-part_file_load_time)))
            reporter.print_console(" Loading %3.2f%% %s \033[K"%((cnt/total*100),msg))
            cnt+=1
        
        if has_valid_sections:
            # given that we have new sections to process
            #get targets
            
            for t in targets:
                t=target_type(t)
                # find out what section type this target wants
                sections=self.GetSectionsBasedOnTarget(t)
                #for each section that that wants to be handled this target
                for section_type in sections:
                    #process that section
                    self.ProcessSection(section_type,t)
        
        self.map_scons_target_list()
        
        
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
        if target.isPartAlias() == False:
            target.all=True
            if target.orginal_string not in ['all','.']:
                reporter.report_warning('Target "%s" is unknown to Parts, it may be known to SCons. Force reading all data'%target.orginal_string)
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
                reporter.report_error("Updating of disk was interrupted!",show_stack=False)
            elif tm.Stopped:
                retcode=4
                reporter.report_error("Errors detected while updating disk!",show_stack=False)
                    
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
            common.g_engine.def_env.Exit(retcode)
        finally:
            for p in part_set:
                p.Vcs.PostProcess()
            datacache.SaveCache(key='vcs')
            
        
    def _add_part(self,object):
        if object.Alias is None:
            self.__to_map_parts.append(object)
            return
        self.__part_count+=1
        object._set_order_value(self.__part_count)
        self.parts[object.Alias]=object
        
    def _clean_unknown(self,known_pobj):
        for i in self.__to_map_parts:
            if i.Name==known_pobj.Name and\
                i.Version==known_pobj.Version and\
                i._kw.get('TARGET_PLATFORM',common.g_engine.def_env['TARGET_PLATFORM']) == known_pobj.Env['TARGET_PLATFORM']:                
                known_pobj._merge(i)
                self.__to_map_parts.remove(i)
                break

    def _setup_out_of_date(self,root_parts):
        '''
        the logic here has to only care about seeing if anything is out of date.
        if anything is we can't return early
        '''
        ret=[]
        cnt=0;
        total=len(root_parts)*1.0+1
        reporter.print_console(" %3.2f%%"%(cnt/total*100))
        for p in root_parts:
            st=time.time()
            reporter.verbose_msg("update_check",'Checking if Part "%s" is up-to-date'%p.Alias)
            # we test to see if the whole Part is up to date
            # if it is not we break
            if self.is_whole_part_up_to_date(p.Alias)==False:
                self.__cache_bad=True
                break
            reporter.verbose_msg("update_check_time","Update check time for %s: %s seconds"%(p.Alias,time.time()-st))
            cnt+=1
            reporter.print_console(" %3.2f%%"%(cnt/total*100))
        reporter.print_console(' 100%%')
        return ret
            
        
        
    def _setup_fast_incremental(self,root_parts):
        '''        
        The logic here will try to figure out what is out of date to allow a faster 
        incremental build. it will return a list of out of date parts that allows
        Parts to know what it load form cache vs reading files ( and or not process at all)
        '''
        out_date_list=[]
        reporter.print_msg("Processing Targets to see what is up-to-date")
        cnt=0;
        total=len(root_parts)*1.0+1
        reporter.print_console(" %3.2f%%"%(cnt/total*100))
        uttt=time.time()
        for p in root_parts:
            st=time.time()
            reporter.verbose_msg("update_check",'Checking if Part "%s" is up-to-date'%p.Alias)
            cache=datacache.GetCache("part-"+p.Alias)
            if cache is None:
                reporter.verbose_msg("update_check","%s is out of date because there no DataCache file"%p.Alias)
                self.__cache_bad=True
                break
            if out_date_list != []:
            # we test to see if this part is up-to-date or not
            #see if the current Part depend on anyting in the out of date list
                for x in cache['full_root_depends']:
                    if x in out_date_list:
                        # this means this part depend on something that is
                        # out of date, so we say it is out of date as well
                        out_date_list.append(p.Alias)
                        # since this part is out of data.. and it could have sub-parts that are out of date
                        # we have to force build the whole object, otherwise it might not become up-to-date
                        #SCons.Script.BUILD_TARGETS.append(p.Alias)
                        reporter.verbose_msg("update_check",'Part "%s" is out of date because it depends on a Part "%s" that is out of date'%(p.Alias,x))
                        continue
            # we store failures as we assume that this is less than
            # one that would pass given common incremental build cases
            if self.is_whole_part_up_to_date(p.Alias)==False:
                out_date_list.append(p.Alias)
                # since this part is out of data.. and it could have sub-parts that are out of date
                # we have to force build the whole object, otherwise it might not become up-to-date
                #SCons.Script.BUILD_TARGETS.append(p.Alias)
            cnt+=1
            reporter.print_console(" %3.2f%% %s is %s                "%(cnt/total*100, p.Alias,p.Alias in out_date_list and "out of data" or "up to date!"))
            reporter.verbose_msg("update_check_time","Update check time for %s: %s seconds"%(p.Alias,time.time()-st))
        reporter.print_console(' 100%%')
        return out_date_list
        
    def _setup_fast_incremental_no_update_check(self,root_parts):
        '''
        This skips checking if the Part that are up to date, minus checking the 
        targets directly. For this to work the targets have to map to a direct 
        Parts object. If it is unknown we build everything. Given that the update
        check are skipped we warn (if we don't build everything) that the build
        outputs may be bad.
        '''
        st=time.time()
        ret=[]
        targets=SCons.Script.BUILD_TARGETS
        for t in targets:
            tmp=self._get_stored_root_alias_from_target(target_type(t))
            if tmp is None:
                # we have an issue as we can't map the target
                # so just assume everything
                self.__cache_bad=True
                break
            else:
                for t in tmp:
                    p=self._from_alias(t)
                    reporter.verbose_msg("update_check",'Checking if Part "%s" is up-to-date'%p.Alias)
                    if self.is_whole_part_up_to_date(p.Alias)==False:
                        ret.append(p.Alias)
                    reporter.verbose_msg("update_check_time","Update check time for %s: %s seconds"%(p.Alias,time.time()-st))
        
        if self.__cache_bad==False and  ret !=[]:
            reporter.report_warning("*******************************************************************************",show_stack=False)
            reporter.report_warning("Update checks on dependents are being skipped, Build may fail or outputs may be corrupted!",show_stack=False)
            reporter.report_warning("*******************************************************************************",show_stack=False)
        
        return ret
        
    def _get_part(self,alias=None, name=None, version=None, target_platform=None):
        '''
        return an existing Part based on name-version( optional Target platform
        or alias value
        '''
        
        if alias and name is None and version is None:
            return self._from_alias(alias)
        elif alias is None and name and version and target_platform is None:
            #try to find it in the unsorted stuff
            for i in self.__to_map_parts:
                if i.Name==name and i.Version==version and i._kw.get('TARGET_PLATFORM',common.g_engine.def_env['TARGET_PLATFORM']) == common.g_engine.def_env['TARGET_PLATFORM']:
                    return i
            # in this case we use the default environment target value
            return self._from_nvp(name,version,common.g_engine.def_env['TARGET_PLATFORM'])
        elif alias is None and name and version and target_platform:
            #try to find it in the unsorted stuff
            for i in self.__to_map_parts:
                if i.Name==name and i.Version==version and i._kw.get('TARGET_PLATFORM',common.g_engine.def_env['TARGET_PLATFORM']) == target_platform:
                    return i
            return self._from_nvp(name,version,target_platform)

        reporter.report_error(
                    "Only alias or name-version-target_platform combination can be used"
                    )
        

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
    
    #def _name_from_refstr(self,refstr):
    #    ''' returns the name of a part the ref string would point to
    #    
    #    @param refstr The string that refers to a part name, such as alias::foo
    #    
    #    This returns a Part name to a root part or None if nothing is found
    #    '''
    #    # clean up more later...
    #    if refstr.startswith('alias::'):
    #        # we have an alias
    #        tmp=self._from_alias(refstr[len('alias::'):])
    #        if tmp:
    #            return tmp.Name
    #        else:
    #            return None
    #    else: 
    #        if refstr.startswith('name::'):
    #            refstr=refstr[len('name::'):]
    #        #else assume name ( assuming it is root??)
    #    
    #        # see if we have a name match
    #        alias_lst=self._alias_list(name)
    #        if alias_lst == []:
    #            return None
    #        return refstr
    
    
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
            for i in local_space:
                pobj=i
                # if we have a match in the local space it has to match, or fail
                if pobj.Name == name:
                    this_ver=pobj.Version
                    if this_ver in ver_range and this_ver >= last_ver and target_platform==pobj._platform_match:
                        last_ver=this_ver
                        ret=pobj
                    else:
                        reporter.report_error
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
                reporter.report_error(
                    '"%s" Alias is not defined, unexcepted error.'%
                    i
                    )
            
            if pobj.Name == name:
                # get the version info
                this_ver=pobj.Version 
                if this_ver in ver_range and this_ver >= last_ver and target_platform==pobj._platform_match:
                    last_ver=this_ver
                    ret=pobj
            
        return ret

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

    def is_whole_part_up_to_date(self,alias):
        ''' 
        this check all the sub parts of the alias root part to see if they 
        are up to date
        '''
        
        def process_sub(sub):
            sub_data=datacache.GetCache("part-"+sub)
            if sub_data is None:            
                reporter.verbose_msg("update_check","%s is out of date because there no DataCache file"%sub)
                self.is_whole_part_up_to_date.cache[sub]=False
                return False
            
            if self.is_part_up_to_date(sub_data['alias']) == False:
                self.is_whole_part_up_to_date.cache[sub]=False
                return False
            
            for sub in sub_data['subparts']:
                if process_sub(sub) == False: return False
            self.is_whole_part_up_to_date.cache[sub]=True
            return True
            
                
        try:
            return self.is_whole_part_up_to_date.cache[alias]
        except AttributeError:
            self.is_whole_part_up_to_date.__dict__['cache']={}
        except KeyError:
            pass
        
        # see if we have data at all for this alias
        data=datacache.GetCache("part-"+alias)
        if data is None:
            
            reporter.verbose_msg("update_check","%s is out of date because there no DataCache file"%alias)
            self.is_whole_part_up_to_date.cache[alias]=False
            return False
        #get the root alias for this guy
        root_alias=data['root_alias']
        return process_sub(root_alias)
            
        
    def is_part_up_to_date(self,alias,check_all=False):
        '''
        see if the alias is up to data
        alias - alias to the part we want to test
        chack_all -- default to false, will check all node, not exit at first failure
        this is useful for verbosing what is not up to date
        '''
        import config
        if check_all == False:
            try:
                return self.is_part_up_to_date.cache[alias]
            except AttributeError:
                self.is_part_up_to_date.__dict__['cache']={}
            except KeyError:
                pass
        data=datacache.GetCache("part-"+alias)
        
        # see if we have a cache file 
        had_error=False
        if data is None:
            reporter.verbose_msg("update_check","%s is out of date because there no DataCache file"%alias)
            if check_all==False: self.is_part_up_to_date.cache[alias]=False
            return False
            
        # see if the part file is different
        if os.path.isfile(data['file']['name']):
            # it should exist
            if node_helpers.node_up_to_date(data['file']) == False:
                if check_all==False: self.is_part_up_to_date.cache[alias]=False
                return False
        else:
            reporter.verbose_msg("update_check",'%s is out of date because file "%s" does not exist'%(alias,data['file']['name']))

        # next we test the build context files
        
        for t,flist in data.get('config_context',{}).items():
            # first check to see if this is the file would use
            cfg_files=config.get_defining_config_files(
                            data['config'],
                            t,
                            platform_info.HostSystem(),
                            platform_info.SystemPlatform(data['target_platform']))
            # check to see that we have the same amount of files
            #print cfg_files,flist
            if len(cfg_files)!=len(flist):
                reporter.verbose_msg("update_check",'%s is out of date because the set of files defining configuration "%s" for tool "%s" are different.'%(alias,data['config'],t))
                if check_all==False: self.is_part_up_to_date.cache[alias]=False
                return False
            for f in flist:
                
                if f['name'] in cfg_files:
                    #this file is in the set of previous found files
                    # check if file has changed
                    if f is not None:
                        if node_helpers.node_up_to_date(f) == False:
                            had_error=True
                            if check_all==False: self.is_part_up_to_date.cache[alias]=False
                            if not check_all: return False        
                else:
                    reporter.verbose_msg("update_check",'%s is out of date because the set of files defining configuration "%s" for tool "%s" are different.\n The file "%s" was not in set of: %s'%(alias,data['config'],t,f['name'],cfg_files))
                    if check_all==False: self.is_part_up_to_date.cache[alias]=False
                    return False
                    
        
        # next we test the build context files
        for t in data.get('build_context',[]):
            if node_helpers.node_up_to_date(t) == False:
                had_error=True
                if check_all==False: self.is_part_up_to_date.cache[alias]=False
                if not check_all: return False

        #test each node that we mapped to this Component
        for t in data.get('nodes',[]):                
            if node_helpers.node_up_to_date(t) == False:
                had_error=True
                if check_all==False: self.is_part_up_to_date.cache[alias]=False
                if not check_all: return False
                
        if had_error: return False
        if check_all==False: self.is_part_up_to_date.cache[alias]=True
        return True


            
    def StoreCacheData(self):
        s=time.time()
        alist=[]
        aset=set([])
        
        
        for p in self.parts.values():
            if p._is_read:
                # figure out if we should save data here
                tmp=datacache.GetCache("part-"+p.Alias)
                # no data cache is a default yes

                if tmp is None:
                    save_data=True
                else:
                    # else are there different node bound to this Component
                    # or did the part file change in some way
                    save_data=len(tmp.get('nodes',[])) != len(p._part_nodes) and \
                     self.is_whole_part_up_to_date(p.Alias) == False
            
                if save_data:
                    # get Keys that effect given part part object
                    #keys=p._get_cache_keys()         
                    # make hash kay value
                    ## fill in
                    # Get data to pickle
                    tmp=p._get_cache_data()
                    # pickle data
                    datacache.StoreData("part-"+p.Alias,tmp)
                else:
                    tmp=datacache.ClearCache("part-"+p.Alias)
                    #print "did not process",p.Alias

                alist.append(p.Alias)
                tmp=datacache.GetCache("part-"+p.Alias)
                aset.update(tmp['alias_set'])
            else:
                tmp=datacache.ClearCache("part-"+p.Alias)
                #print "did not process",p.Alias
                
        print "Time to create data=",time.time()-s
        return alist,aset
        
            
            
            
            
        
