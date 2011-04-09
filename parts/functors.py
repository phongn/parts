import glb
import common
import api.output

import SCons.Script

import thread

class map_parts_alias(object):
    '''
    This class maps the high level alias with other high level alias. This is a very important function 
    used to make sure that SCONS knows that subparts and part relations. Scons only sees these relations
    as the mapping of high level Aliases. Scons doesn't have a concept of a part or component. Without
    this the "idea" that a dependent part should full build will not happen, only stuff that SCons sees
    as being needed will build. Scons is fully correct in its actions, but many user find this behavor
    subjectivly non-obvious when we add the parts/component idea. This allow us to gain a better sense
    of order by tell scons that you need to do the other stuff as well, while letting Scons do what it
    knows is best, in the order if thinks is best. Note there there is a part 2 to this. In the file
    version mapping ie pieces/version_mapping.py we have something simular to this to allow for tell
    Scons to correctly clean this mess off the disk.
    '''
    def __init__(self,env):
        self.env=env
        #self.value=value
    def __call__(self):
        pass
        #pobj=glb.engine._part_manager._from_env(self.env)
        #dlst=pobj.Depends
        #flist=[]
        #flist2=[]
        #for d in dlst:
        #    #get unknown alias
        #    val=d.resolve_alias(self.env)
        #    if val == "" or val is None:
        #        api.output.warning_msg('Part "{0}" depends on "{1}", however this Parts was not defined.'.format(self.env.subst('$PART_NAME'),d.name),stackframe=d.stackframe)
        #        continue
        #    denv=pobj.Env
        #    flist.append(denv.subst('${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}')+val)
        #    #flist2.append(denv.subst('${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}')+val)
        ##the build alias
        #build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}'
        ### this one might help SCons scale better with larger -j values
        ##the install alias
        ##install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}'
        ## we map the build alias to the dependent SDK aliases
        #self.env.Alias(build_alias,flist)
        ## we map the install alias to the dependent INSTALL aliases
        ## self.env.Alias(install_alias,flist2)


def full_parts_depends_list(env):
    ''' make a full depends list ( internal and non internal) for the given Env
    We will probally want to refactor some of this into state in def_env later
    '''
    
    pobj=glb.engine._part_manager._from_env(env)
    
    cache_tmp=pobj.FullDepends
    if cache_tmp is None:
        dlst=pobj.Depends
        flst=[]
        for d in dlst:
            val=d.resolve_alias(env)
            if val == "":
                continue
            flst.append(val)
            
            tmp_env=glb.engine._part_manager._from_alias(val).env
            tmp=full_parts_depends_list(tmp_env)
            flst.extend(tmp)
            pobj.set_full_depends(flst)
    else:
        flst=cache_tmp
    return flst


def gen_rpath_link(sec):
    '''
    Add the Rlink path that woudl be added for the component depending on this 
    component, Not what this component would depend on
    '''
    import mappers
    
    dlst=sec.Depends
    env=sec.Env
    rplst=[]

    # setup the current alias case 
    # this adds what this componnet directly depends on
    # not what it dependents depend on which is what we need for the 
    # rpath-link case
    # get the libpath for this component
    plist=mappers.sub_lst(env,env.get('LIBPATH',[]),thread.get_ident())
    for p in plist:
        rp='-Wl,-rpath-link='+env.Dir(p).path
        common.append_unique(rplst,rp)
                    
    # setup everything that we depend on that we may not have added yet
    for d in dlst:
        if d.PartRef.hasUniqueMatch:
            try:
                # try to get a cached value
                rtmp=d.Section._cache['rlink']
            except KeyError:
                # generate the values
                rtmp=gen_rpath_link(d.Section)
                
            for i in rtmp:
                common.append_unique(rplst,i)
            sec._cache['rlink']=rplst
            
        elif d.PartRef.hasMatch ==False:
            api.output.warning_msg("Failed to map dependency for {0} when mapping -rpath-link data because:\n {1}".format(sec.Part.PartName,d.PartRef.NoMatchStr()),show_stack=False)
        elif d.PartRef.hasAmbiguousMatch:
            api.output.warning_msg("Failed to map dependency for {0} when mapping -rpath-link data because:\n {1}".format(sec.Part.PartName,d.PartRef.NoMatchStr()),show_stack=False)
    return rplst
    

class map_rpath_link_part(object):
    ''' this class is used to map the rpath-link option to the LINKFLAGS on linux
    like systems by pulling information of the LIBPATH.
    '''
    def __init__(self,env,sec):
        self.env=env
        self.sec=sec
        
    def __call__(self):
        if self.env['AUTO_RPATH']==True:
            rplst=gen_rpath_link(self.sec)
            self.env.AppendUnique(LINKFLAGS=rplst,delete_existing=True)


class map_rpath_part(object):
    '''This class adds to the RPATH value based on location of where there .SO
    are stored.. classically in a seperate INSTALL_LIB directory. This allow for correct
    running of the program after a build without special setup'''
    def __init__(self,env,add_self=False):
        self.env=env
        self.add_self=add_self
    def __call__(self):
        # do we want to auto generate RPATH information
        if self.env['AUTO_RPATH']==True:
            rlst=self.env.get('RPATH',[])
            # make a mapping between the bin and lib directories
            rlst.append(self.env.Literal('\'$$ORIGIN/'+common.relpath(self.env.Dir('$INSTALL_LIB').path,self.env.Dir('$INSTALL_BIN').path)+'\''))
            self.env['RPATH']=rlst            
          
class map_build_context(object):
    ''' 
        This maps all build info related files we might need to help detect quickly
    if the build context has changed from the last run.
    '''
    def __init__(self,pobj):
        self.pobj=pobj
        
    def __call__(self):
        
        self.pobj._build_context_files.update(self.pobj.Env['_BUILD_CONTEXT_FILES'])
        self.pobj._config_context_files.update(self.pobj.Env['_CONFIG_CONTEXT'])
        
        
class map_depends(object):
    def __init__(self,env,partref,tsection,key,stack):
        self.env=env
        self.partref=partref
        self.tsection=tsection
        self.key=key
        self.stack=stack
        
    def __call__(self):
                
        if self.partref.hasUniqueMatch:
            pobj=self.partref.Matches[0]
            sec=pobj.Section(self.tsection)
        elif self.partref.hasMatch ==False:
            api.output.error_msg("Failed to map dependency for {0} because:\n {1}".format(self.env.subst('$PART_NAME'),self.partref.NoMatchStr()),stackframe=self.stack)
        elif self.partref.hasAmbiguousMatch:
            api.output.error_msg("Failed to map dependency for {0} because:\n {1}".format(self.env.subst('$PART_NAME'),self.partref.AmbiguousMatchStr()),stackframe=self.stack)
        
        #if self.key in sec.ExportAsDepends:
        sec.esigs()
        if sec.Exports.get(self.key) and ("INSTALL" in self.key or "SDK" in self.key):
            alias="{0}::alias::{1}".format(self.env['PART_SECTION'],self.env['PART_ALIAS'])
            alias1="{0}::alias::{1}::{2}".format(self.env['PART_SECTION'],self.env['PART_ALIAS'],self.key)
            alias2="{0}::alias::{1}::{2}".format(self.tsection,pobj.Alias,self.key)
            self.env.Alias(alias,self.env.Alias(alias1))
            self.env.Alias(alias1,self.env.Alias(alias2))
        
          
        
# add configuartion varaible
api.register.add_bool_variable('AUTO_RPATH',True,'Controls if RPath values are automatically added to path')

