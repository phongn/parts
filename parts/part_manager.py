import common
import parts
import reporter
import datacache
import node_helpers
import platform_info
from target_type import target_type

import SCons.Script
import time
import os

import SCons.Job
 

class vcs_task(object):
    ''' 
    This is a simple class that does nothing more than have the Part update
    itself on disk. This is used to for parallel checkouts/updates.
    '''
    def __init__(self,part):
        self.part = part
        
    def prepare(self):
        pass
        
    def needs_execute(self):
        ''' this always need to execute'''
        return 1
    
    def execute(self):
        ''' this is what we call to do the checkout'''
        self.part.UpdateOnDisk()
        
    def exception_set(self):
        pass
        
    def failed(self):
        pass
        
    def executed(self):
        pass

    def postprocess(self):
        pass


class vcs_taskmaster(object):
    def __init__(self):
        self.__i = 0
        self.__tasks = []
    def append(self,x) :
        if x is None:
            self.__tasks.append(None)
        else:
            self.__tasks.append(vcs_task(x))
    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t
    def stop(self):
        pass
    def cleanup(self):
        pass
    def _has_tasks(self):
        return self.__tasks != []
    
class part_manager(object):
    
    def __init__(self):
        self.sections=common.g_sections
        self.parts={} # a dictionary of all parts objects by there alias value
        self.name_to_alias={} #a dictionary of a known Parts name and possible alias that match
        self.__to_map_parts=[] # stuff that needs to be mapped, else it is wasted space
        self.__cache_bad=False # used to help prevent wasting time on cases of incomplete cache data
    
    def _get_stored_root_alias(self,alias):
        '''
        Given the alias and based on stroed data what is the root part alias 
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
            elif alias in tmp['alias_set']:
                # if it is we have a match
                #store the root alias for this part
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
        self._add_part(tmp.Alias,tmp)   
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
                self._add_part(tmp.Alias,tmp)
                self._load_part_from_cache(tmp)
                tmp._map_alias()
                
    
    def ProcessParts(self):
        ''' 
        This function will process all the Parts object based on the targets
        '''
        
        has_valid_sections=False
        targets=SCons.Script.BUILD_TARGETS
        # check to see that we even have targets to process
        if targets == []:
            return 
        
        # see if the --use-sdk option is set
        #use_sdk=SCons.Script.GetOption('use_sdk')

        #given that the context should be good
        # try to map the target to a known Part
        reporter.print_msg("Processing Targets to find known reduce set of Parts objects to define")
        root_parts=[]
        for t in targets:
            tmp=self._get_stored_root_alias(t)
            if tmp is None:
                # we have a unknown target
                # note we could test all parts files to see if they changed
                # this would allow us to know if target could be cached safely
                root_parts=[]
                break
            else:            
                #for each root alias we have we want to add the set of root parts
                # this this part and any sub parts it might have
                for t in tmp:
                    common.extend_unique(root_parts,[t]+self._get_stored_full_root_depends(t))
        
        print root_parts
        # if we don't have any root parts.. read everything
        if root_parts == []:
            root_parts = self.parts.values()
        else:
            # we have root parts.. pull these objects in to the list to process
            tmp=[]
            for i in root_parts:
                try:
                    tmp.append(self.parts[i])
                except KeyError:
                    reporter.verbose_msg('part_manager',"%s was not found in set of Root Part defined, global cache out of date?"%(i))
            root_parts=tmp
            
        def pcmp(x,y):
            if x.Alias == y.Alias: return 0
            xcache=datacache.GetCache("part-"+x.Alias)
            ycache=datacache.GetCache("part-"+y.Alias)
            
            if ycache:
                # Y uses X
                xiny = x.Alias in ycache['full_root_depends']
            else:
                xiny=False
            if xcache:
                # X uses Y
                yinx = y.Alias in xcache['full_root_depends']
            else:
                yinx=False
            if xiny and yinx: 
                # if we got here we need to see is the User said if the Part
                # uses the other part.. needed for classic format ordering issues
                # the new format is not effect by this
                if x._uses_part(y): return 1
                elif y._uses_part(x): return -1
                else:return cmp(x.Alias,y.Alias)
            elif xiny: return -1
            elif yinx: return 1
            
            return cmp(x.Alias,y.Alias)
            
        #is everything up to date on disk update file on disk?
        self.UpdateOnDisk(  )
        
        # update check.. here we will:
        # 1) try to see if we can exit early cause everything is up-to-date
        # 2) try to figure out if everything is not up-to-date what can be loaded from the cache
        # 3) try order the parts a little based on known depends ordering
        
        # for classic formats mainly... only works if we have datacache stored
        # or if the part has a direct toplevel depends statement in the Part
        # creation call. For new style Parts this might help, or is pointless 
        root_parts.sort(pcmp)
        if self.__cache_bad==False and common.g_engine._build_mode=='build':
            out_date_list=[]
            uttt=time.time()
            if SCons.Script.GetOption("incremental-cache"):
                #select some type of fast incremtail logic
                if SCons.Script.GetOption("incremental-dependent-checks"):
                    out_date_list=self._setup_fast_incremental_no_update_check(root_parts)
                else:
                    out_date_list=self._setup_fast_incremental(root_parts)
                    
                    
            elif SCons.Script.GetOption("update_check_exit"):
                out_date_list=self._setup_out_of_date(root_parts)
                
                       
            reporter.verbose_msg("update_check_time","Total Time for update check: %s seconds"%(time.time()-uttt))
            if out_date_list == [] and self.__cache_bad==False and SCons.Script.GetOption("update_check_exit"):
                reporter.print_msg("Everything seem to be up-to-date. Shutting down...")
                common.g_engine.def_env.Exit(0)
            
        
        read_start=time.time()
        
        for p in root_parts:
            
            # we go through all defined root parts
            if self.__cache_bad==False and p.Alias not in out_date_list:
                cache=datacache.GetCache("part-"+p.Alias)
                reporter.print_msg("%s is up-to-date loading cache"%p.Alias)
                p._setup_from_cache_data(cache)
                self._load_part_from_cache(p)
                p._map_alias()

            else:
                reporter.print_msg("%s is out-of-date loading part file"%p.Alias)
                p.ReadFile()
                self._clean_unknown(p)
            
                # figure out if this part is new style or old style
                valid_sec=self.hasValidSection(p)
                if not p._hasTargetFiles() and valid_sec:
                    #print "new format",p.Name
                    p._set_part_format('new')
                    # new format
                    has_valid_sections=True
                elif p._hasTargetFiles() and valid_sec:
                    # mixed
                    #print "mixed",p.Name
                    pass
                elif p._hasTargetFiles() and not valid_sec:
                    #old format
                    # if old format we have also processed the part
                    #print "old",p.Name
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
        
    def UpdateOnDisk(self):
        # we need to see if any part needs to be checked out or updated
        #loop each part and ask it need to be updated
        p_list=vcs_taskmaster()
        s_list=vcs_taskmaster()
        for p in self.parts.values():
            # if so add to queue for checkout
            if p.VcsNeedsToUpdate():
                # we check to see if the vcs object allow for the 
                # parallel checkout policy.
                if p.VcsAllowParallelProcessing():
                    p_list.append(p)
                else:
                    s_list.append(p)
                    
        #checkout anything in the queue
        if p_list._has_tasks():
            # get value for level of number of concurrent checkouts
            vcs_j=SCons.Script.GetOption('vcs_jobs')
            if vcs_j == 0:
                vcs_j=SCons.Script.GetOption('num_jobs')
            p_list.append(None)
            jobs = SCons.Job.Jobs(vcs_j, p_list)
            jobs.run()
        if s_list._has_tasks():
            p_list.append(None)
            jobs = SCons.Job.Jobs(1, s_list)
            jobs.run()
        
    def _add_part(self,key,object):
        if key is None:
            self.__to_map_parts.append(object)
            return
        self.parts[key]=object
        
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
        for p in root_parts:
            st=time.time()
            reporter.verbose_msg("update_check",'Checking if Part "%s" is up-to-date'%p.Alias)
            # we test to see if the whole Part is up to date
            # if it is not we break
            if self.is_whole_part_up_to_date(p.Alias)==False:
                self.__cache_bad=True
                break
            reporter.verbose_msg("update_check_time","Update check time for %s: %s seconds"%(p.Alias,time.time()-st))
        return ret
            
        
        
    def _setup_fast_incremental(self,root_parts):
        '''        
        The logic here will try to figure out what is out of date to allow a faster 
        incremental build. it will return a list of out of date parts that allows
        Parts to know what it load form cache vs reading files ( and or not process at all)
        '''
        out_date_list=[]
        reporter.print_msg("Processing Targets to see what is up-to-date")
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
                        SCons.Script.BUILD_TARGETS.append(p.Alias)
                        reporter.verbose_msg("update_check",'Part "%s" is out of date because it depends on a Part "%s" that is out of date'%(p.Alias,x))
                        continue
            # we store failures as we assume that this is less than
            # one that would pass given common incremental build cases
            if self.is_whole_part_up_to_date(p.Alias)==False:
                out_date_list.append(p.Alias)
                # since this part is out of data.. and it could have sub-parts that are out of date
                # we have to force build the whole object, otherwise it might not become up-to-date
                SCons.Script.BUILD_TARGETS.append(p.Alias)
            reporter.verbose_msg("update_check_time","Update check time for %s: %s seconds"%(p.Alias,time.time()-st))
            
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
            tmp=self._get_stored_root_alias(t)
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
                    if this_ver in ver_range and this_ver > last_ver and target_platform==pobj._platform_match:
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
                if this_ver in ver_range and this_ver > last_ver and target_platform==pobj._platform_match:
                    last_ver=this_ver
                    ret=pobj
                                
            
        return ret

    def _alias_list(self,name):
        '''
        given an a part name return a list of all parts alias that 
        could be matches for that name
        '''
        return self.name_to_alias.get(name,set([]))
    
    def add_name_alias(self,name,alias):
        try:
            self.name_to_alias[name].add(alias)
        except KeyError:
            self.name_to_alias[name]=set()
            self.name_to_alias[name].add(alias)

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
            #if "utest@" not in alias:
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
                    reporter.verbose_msg("update_check",'%s is out of date because the set of files defining configuration "%s" for tool "%s" are different.'%(alias,data['config'],t))
                    if check_all==False: self.is_part_up_to_date.cache[alias]=False
                    return False
                    
        
        # next we test the build context files
        for t in data.get('build_context',[]):
            if node_helpers.node_up_to_date(t) == False:
                had_error=True
                if check_all==False: self.is_part_up_to_date.cache[alias]=False
                if not check_all: return False

        #test each node that we mapped to this Component
        for t in data['nodes']:                
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
                    save_data=len(tmp['nodes']) != len(p._part_nodes) and \
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
        
            
            
            
            
        
