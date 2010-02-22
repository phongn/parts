import common
import SCons.Script
import reporter

class map_parts_alias:
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
        
        alias=self.env['ALIAS']
        def_env=SCons.Script.DefaultEnvironment()

        dlst=def_env['PART_INFO'][alias]['DEPENDSON']
        flist=[]
        flist2=[]
        for d in dlst:
            #get unknown alias
            val=d.resolve_alias(self.env)
            if val == "":
                continue
            denv=def_env['PART_INFO'][val]['ENV']
            flist.append(denv.subst('${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}')+val)
            flist2.append(denv.subst('${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}')+val)
        #the build alias
        build_alias='_${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
        ## this one might help SCons scale better with larger -j values
        #the install alias
        install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
        # we map the build alias to the dependent SDK aliases
        self.env.Alias(build_alias,flist)
        # we map the install alias to the dependent INSTALL aliases
        self.env.Alias(install_alias,flist2)


def full_parts_depends_list(env):
    ''' make a full depends list ( internal and non internal) for the given Env
    We will probally want to refactor some of this into state in def_env later
    '''
    alias=env['ALIAS']
    def_env=SCons.Script.DefaultEnvironment()
    cache_tmp=def_env['PART_INFO'][alias].get('FULL_DEPENDS',None)
    if cache_tmp is None:
        dlst=def_env['PART_INFO'][alias]['DEPENDSON']
        flst=[]
        for d in dlst:
            val=d.resolve_alias(env)
            if val == "":
                continue
            flst.append(val)
            
            tmp_env=def_env['PART_INFO'][val]['ENV']
            tmp=full_parts_depends_list(tmp_env)
            flst.extend(tmp)
            def_env['PART_INFO'][alias]['FULL_DEPENDS']=flst
    else:
        flst=cache_tmp
    return flst


def gen_rpath_link(alias):
    '''
    Add the Rlink path that woudl be added for the component depending on this 
    component, Not what this component would depend on
    '''
    import mappers
    def_env=SCons.Script.DefaultEnvironment()
    pinfo=def_env['PART_INFO'][alias]
    dlst=pinfo['DEPENDSON']
    env=pinfo['ENV']
    rplst=[]

    # setup the current alias case 
    # this adds what this componnet directly depends on
    # not what it dependents depend on which is what we need for the 
    # rpath-link case
    # get the libpath for this component
    plist=mappers.sub_lst(env,env.get('LIBPATH',[]),def_env)
    for p in plist:
        rp='-Wl,-rpath-link='+env.Dir(p).path
        common.append_unique(rplst,rp)
                    
    # setup everything that we depend on that we may not have added yet
    for d in dlst:
        d_alias=d.resolve_alias(env)
        if d_alias == '':
            reporter.report_warning("Part name ["+d.name+"] is not defined for mapping RPATH data",
                                        print_once=True,
                                        )
            continue
        try:
            rtmp=def_env['PART_INFO'][d_alias]['RLINK_CACHE']
            # add saved data
            for i in rtmp:
                common.append_unique(rplst,i)
        except KeyError:
            rtmp=gen_rpath_link(d_alias)
            for i in rtmp:
                common.append_unique(rplst,i)
    # data to cache for any component that depend on this component
    pinfo['RLINK_CACHE']=rplst # add this case to the cache
    return rplst
    

class map_rpath_link_part:
    ''' this class is used to map the rpath-link option to the LINKFLAGS on linux
    like systems by pulling information of the LIBPATH.
    '''
    def __init__(self,env):
        self.env=env
        
    def __call__(self):
        if self.env['AUTO_RPATH']==True:
            def_env=SCons.Script.DefaultEnvironment()
            alias=self.env['ALIAS']
            rplst=gen_rpath_link(alias)
            self.env.AppendUnique(LINKFLAGS=rplst,delete_existing=True)


class map_rpath_part:
    '''This class adds to the RPATH value based on location of where there .SO
    are stored.. classically in a seperate INSTALL_LIB directory. This allow for correct
    running of the program after a build without special setup'''
    def __init__(self,env,add_self=False):
        self.env=env
        self.add_self=add_self
    def __call__(self):
        if self.env['AUTO_RPATH']==True:
            import mappers
            rlst=self.env.get('RPATH',[])
            def_env=SCons.Script.DefaultEnvironment()
            alias=self.env['ALIAS']
            #print alias
            dlst=def_env['PART_INFO'][alias]['DEPENDSON']
            if self.add_self==True:
                temp=self.env.Component(def_env['PART_INFO'][alias]['NAME'],
                self.env.subst(str(def_env['PART_INFO'][alias]['VERSION'])))
                dlst=[temp]+dlst #################### need to fix this for linux
            #print "Start",self.env['ALIAS'],rplst
            for i in dlst:
                val=self.env.subst(i.alias_mapping_string())
                if val == "":
                    continue
                plist=mappers.sub_lst(self.env,["${PARTS('"+val+"','LIBPATH',True)}"],def_env)
                for p in plist:
                    r=self.env.Literal('\'$$ORIGIN/'+common.relpath(self.env.Dir('$INSTALL_LIB').path,self.env.Dir('$INSTALL_BIN').path)+'\'')
                    #r=relpath(self.env.Dir(p).path,self.env.Dir('$OUT_BIN').path)
                    if r not in rlst:
                        rlst.append(r)
                        #print ' \t',r
            rlst=common.make_unique_str(rlst)
            self.env.Replace(RPATH=rlst)
            #print 'RPATH LIST',self.env['RPATH']
          
# add configuartion varaible
common.AddBoolVariable('AUTO_RPATH',True,'Controls if RPath values are automatically added to path')

