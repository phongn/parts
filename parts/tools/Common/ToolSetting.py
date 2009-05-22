
import parts.platform_info as platform_info
import parts.common as common
import copy

'''
This class handles mangament of tool info objects based on HOST and TARGET 
platform support.

The main logic caches data based on exist or query calls. If the request for
a version is None, it will do a query ( check for all possible cases)
If the version is exact, it will test for the exact version, However the tool
info might still do a limited query. ( this happens in cases of tools that 
support many drops that are side by side installable. ie request for version 9
means then find best match, which spawns match for all version matches)

To help with speed a cache is made of found versions. 
a seperate items value is saved to say if the cache is a full query or not.
This allow the ability to retest 

'''


class ToolSetting:
    def __init__(self,name):
        
        # used as the namespace for common values such as version and script
        self.name=name.upper() 
        # <name>_VERSION
        self.version_tag=self.name+'_VERSION'
        # <name>_SCRIPT
        self.script_tag=self.name+'_SCRIPT'
        # <name>_ROOTPATH
        self.rootpath_tag=self.name+'_INSTALL_ROOT'

        #supported tools
        self.tools={} 
        
        # tools that we found
        self.found={}
        # tools that we have not found basic same layout given
        #if key value is None this means a full query has been done for 
        #this case, else it is list of versions not found
        self.not_found={}
        
        # all the requested shell env
        # cached in case we are asked again
        self.shell_cache={}## moved to tool_info
    
    def get_cache_key(self,env):
        ''' 
        make a cache/hash key for use to safely store a retrieve data about 
        what we know or don't know at this time.
        '''
        version=env.get(self.version_tag,'None')
        root_path=env.get(self.rootpath_tag,'None')
        use_script=str(env.get(self.script_tag,'False'))
        # Scons 1.3 should be moving to TARGET_OS and TARGET_ARCH.. so we check 
        # for them as well
        target=env.get('TARGET_SYSTEM',env.get('TARGET_OS',"")+'-'+env.get('TARGET_ARCH',""))
        return str(version)+root_path+use_script+str(target)
    
    def get_latest_known_version(self,cache_key): 
        try:
            # assumes presorted when added
            return self.found[cache_key][0]
        except KeyError:
            pass
        except IndexError:
            pass
        return None
        
    def is_version_known(self,version,cache_key): 
        ''' 
        see if the tool is known in our 'found' cache
        assumes that we had called query_for_known already   
        '''
        try:
            return (version in self.found[cache_key])
        except KeyError:
            return False

    def query_for_known(self,env,key):
        '''
        This will query for known defaults based on enviroment value that 
        could have been set by the user such as the <tool>_INSTALL_ROOT or
        <tool>_USE_SCRIPT. It will cache this data to help speed up the build.
        This should not be an issue as the scripts and environment should not
        change during the build. scripts should have a unique path
        '''
        
        # see if we have tested for it
        try:
            if self.not_found[key] is None:
                #this combo was fully queried
                return
        except:
            pass
        # don't have it, so we setup to get it added to cache
        self.found[key]=[]
        self.not_found[key]=None # set this to fully queried
        # setup target to test for
        target=env['TARGET_SYSTEM']
        t1=copy.copy(target)
        t1.Architecture='any'
        t2=copy.copy(target)
        t2.Platform='any'
        t3=copy.copy(t2)
        t3.Architecture='any'            
        
        # test values    
        
        version=env.get(self.version_tag,None)
        root_path=env.get(self.rootpath_tag,None)
        use_script=env.get(self.script_tag,False)
        # make sure we have a target key
        if not self.found.has_key(target):
            self.found[key]=[]
        #test raw target
        if self.tools.has_key(target):
            for k,v in self.tools[target].items():
                tmp=v.query(env,self.name,root_path,use_script)
                if tmp is not None:
                    for ver,senv in tmp.items():
                        self.found[key].append(ver)
                        cache_key=str(version)+key
                        self.shell_cache[cache_key]=senv
        #test for <platform>-any
        if self.tools.has_key(t1):
            for k,v in self.tools[target].items():
                tmp=v.query(env,self.name,root_path,use_script)
                if tmp is not None:
                    for ver,senv in tmp.items():
                        self.found[key].append(ver)
                        cache_key=str(version)+key
                        self.shell_cache[cache_key]=senv
        #test for any-<Arch>
        if self.tools.has_key(t2):
            for k,v in self.tools[target].items():
                tmp=v.query(env,self.name,root_path,use_script)
                if tmp is not None:
                    for ver,senv in tmp.items():
                        self.found[key].append(ver)
                        cache_key=str(version)+key
                        self.shell_cache[cache_key]=senv
        #test for any-any
        if self.tools.has_key(t3):
            for k,v in self.tools[target].items():
                tmp=v.query(env,self.name,root_path,use_script)
                if tmp is not None:
                    for ver,senv in tmp.items():
                        self.found[key].append(ver)
                        cache_key=str(version)+key
                        self.shell_cache[cache_key]=senv                    
        self.found[key].sort(reverse=True)
        
        
    def query_for_exact(self,env,key,version):
        '''
        This will query for known defaults based on enviroment value that 
        could have been set by the user such as the <tool>_INSTALL_ROOT or
        <tool>_USE_SCRIPT. It will cache this data to help speed up the build.
        This should not be an issue as the scripts and environment should not
        change during the build. scripts should have a unique path
        '''
        
        # see if we have tested for it
        try:
            if self.not_found[key] is None:
                #this combo was fully queried
                return
        except:
            pass
        # don't have it, so we setup to get it added to cache
        if not self.found.has_key(key):
            self.found[key]=[]
            self.not_found[key]=[]
            
        # setup target to test for
        target=env['TARGET_SYSTEM']
        t1=copy.copy(target)
        t1.Architecture='any'
        t2=copy.copy(target)
        t2.Platform='any'
        t3=copy.copy(t2)
        t3.Architecture='any'            
        
        # test values    
        cache_key=str(version)+key
        root_path=env.get(self.rootpath_tag,None)
        use_script=env.get(self.script_tag,False)
        
        #test raw target
        if self.tools.has_key(target):
            for k,v in self.tools[target].items():
                if version in v.version_set():
                    tmp=v.exists(env,self.name,version,root_path,use_script)
                    if tmp is not None:
                        self.found[key].append(version)
                        self.shell_cache[cache_key]=tmp
                        self.found[key].sort(reverse=True)
                        return
                        
        #test for <platform>-any
        if self.tools.has_key(t1):
            for k,v in self.tools[target].items():
                if version in v.version_set():
                    tmp=v.exists(env,self.name,version,root_path,use_script)
                    if tmp is not None:
                        self.found[key].append(version)
                        self.shell_cache[cache_key]=tmp
                        self.found[key].sort(reverse=True)
                        return
        #test for any-<Arch>
        if self.tools.has_key(t2):
            for k,v in self.tools[target].items():
                if version in v.version_set():
                    tmp=v.exists(env,self.name,version,root_path,use_script)
                    if tmp is not None:
                        self.found[key].append(version)
                        self.shell_cache[cache_key]=tmp
                        self.found[key].sort(reverse=True)
                        return
        #test for any-any
        if self.tools.has_key(t3):
            for k,v in self.tools[target].items():
                if version in v.version_set():
                    tmp=v.exists(env,self.name,version,root_path,use_script)
                    if tmp is not None:
                        self.found[key].append(version)
                        self.shell_cache[cache_key]=tmp
                        self.found[key].sort(reverse=True)
                        return                   
        self.not_found[key].append(version)
        
        
    def Exists(self,env,tool=None,**kw):
        '''
        primary user function to see if what we want exists
        '''
        # clone env so we test with out messing up current state
        tenv=env.Clone(**kw)
        #get cache key for this enviroment setup
        key=self.get_cache_key(tenv)

        #Get version value
        version=env.get(self.version_tag,None)
        if version is None:
            #if none we query for all
            # do query for all known that match this setup
            self.query_for_known(tenv,key)
            # set version to latest found
            version=self.get_latest_known_version(key)
        else:
            # query for exact match
            self.query_for_exact(tenv,key,version)
        
        #test to see if it was found
        found=self.is_version_known(version,key)
        if tool is not None and found == True:
            try:
                tpath=self.get_shell_env(env)['PATH']
                tmp=SCons.Util.WhereIs(tool,path=tpath)
                if tmp is not None:
                    found = True
            except:
                found=False
                
        #test to see if it was found
        return found

    def GetInfo(self,version,target):
        '''
        Get the information. It is expected that the caller has done the 
        correct tests to validate that the can get information out of this 
        info object correctly, or that it exists.
        '''
        import copy
        t1=copy.copy(target)
        t1.Architecture='any'
        t2=copy.copy(target)
        t2.Platform='any'
        # we try to get the supported information
        # based on best match. 
        #Platform is given priority to architecture
        try:
            #Platform-Architecture
             return self.tools[target][version]
        except KeyError:
            try:
                #Platform-any
                return self.tools[t1][version]
            except KeyError:
                try:
                    #any-Architecture
                    return self.tools[t2][version]
                except KeyError:
                    try:
                        #any-any
                        t2.Architecture='any'
                        return self.tools[t2][version]
                    except KeyError:
                        pass
        return None
        
    def Register(self,hosts,targets,info):
        '''
        Called by user to register a given set of Tool Information objects
        that support some build host and target combination
        '''
        
        hosts=common.make_list(hosts)
        targets=common.make_list(targets)
        info=common.make_list(info)
        
        # iterate all the hosts ignore items that are no supported on current host
        for h in hosts:
            # only need to find first match as all other host would be different
            if h == platform_info.HostSystem():
                tmp={}
                # orginize the versions for easy access later
                for i in info:
                    tmp[i.version]=i
                #add info sorted in to correct target buckets
                for t in targets:  
                    try:
                        self.tools[t].update(tmp)
                    except KeyError:
                        self.tools[t]=tmp
                    
                    
                break
    
    def get_shell_env(self,env):
        ''' 
        This function returns the shell enviroment to be merged into the 
        final SCons environment
        
        The trick with this function is that it really just gets data that was
        stored with the exists call. The data cached here tell us if there is
        a match or not. The Key holds data on everything but the version
        the cache_key adds the version
        '''
        
        
        #get cache key for this enviroment setup
        key=self.get_cache_key(env)
        version=env.get(self.version_tag,None)
        cache_key=str(version)+key
        self.query_for_known(env,key)

        try:
            return self.shell_cache[cache_key]
        except KeyError:
            # basic info we will need
            tinfo=None
            
            root_path=env.get(self.rootpath_tag,None)
            use_script=env.get(self.script_tag,False)
            target=env['TARGET_SYSTEM']
            ##get the tool info for the host-target combo for the requested version
            #print "**",self.found
            #get latest found version if not provided
            if version is None:
                version=self.get_latest_known_version(key)

            # see if we know if the give version exists
            if self.is_version_known(version,key):
                tinfo=self.GetInfo(version,target)
            else:
                # this is an error, nothing found
                # report that version is not found and the versions if any that
                # have been found
                raise ValueError("Version of "+str(version)+" not found. Known version are "+str(self.found[key]))
                
                
            ##got the tool info now get the data
            
            #get the shell environment
            shell_env=tinfo.get_shell_env(env,self.name,version,root_path,use_script)
            
            # store it in cache
            self.shell_cache[cache_key]=shell_env
                
        return shell_env
            
    def MergeShellEnv(self,env):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.__dict__)

        version=env.get(self.version_tag,None)
        shell_env=self.get_shell_env(env)
        if shell_env is None:
            #report error
            pass
            
        # Add data to env
        for k, v in shell_env.items():
            env.PrependENVPath(k, v, delete_existing=1)
        
        ## setup any common state
        #setup version info
        ##if version is None:
        ##    env[self.version_tag]=env[self.name]['VERSION']
        ##if version is None:
        ##    env[self.rootpath_tag]=env[self.name]['INSTALL_ROOT']
    
    