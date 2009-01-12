import common
import SCons.Script

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
        rpt=def_env['PARTS_REPORTER']
        dlst=def_env['PART_INFO'][alias]['DEPENDSON']
        flist=[]
        flist2=[]
        for d in dlst:
            #get unknown alias
            val=d.resolve_alias(self.env)
            if val == "":
                #rpt.part_warning(self.env,"Was not able to map "+d.alias_mapping_string(),True)
                rpt.part_warning(self.env,"Was not able find Part name ["+d.name+"] with version ["+str(d.version)+"]",True)
                continue
            denv=def_env['PART_INFO'][val]['ENV']
            flist.append(denv.subst('${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}')+val)
            flist2.append(denv.subst('${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}')+val)
        #the build alias
        build_alias='_${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
        ## this one might help SCons scale better with larger -j values
        #build_alias='_${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
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
    dlst=def_env['PART_INFO'][alias]['DEPENDSON']
    flst=[]
    rpt=def_env['PARTS_REPORTER']
    for d in dlst:
        val=env.subst(d.alias_mapping_string())
        if val == "":
            #rpt.part_warning(env,"Was not able to map "+d.alias_mapping_string(),True)
            rpt.part_warning(env,"Was not able find Part name ["+d.name+"] with version ["+str(d.version)+"]",True)
            continue
        flst.append(val)
        #print alias,d.alias_mapping_string()
        tmp_env=def_env['PART_INFO'][val]['ENV']
        tmp=full_parts_depends_list(tmp_env)
        flst.extend(tmp)
    return flst

class map_rpath_link_part:
    ''' this class is used to map the rpath-link option to the LICKFLAGS on linux
    like systems by pulling information of the LIBPATH.
    '''
    def __init__(self,env,add_self=False):
        self.env=env
        self.add_self=add_self
    def __call__(self):
        if common.g_args['AUTO_RPATH']==True:
            import mappers
            def_env=SCons.Script.DefaultEnvironment()
            #alias=self.env['ALIAS']
            rplst=self.env.get('LINKFLAGS',[])
            #print 'rpath-link mapping of',alias
            dlst=full_parts_depends_list(self.env)
            if self.add_self==True:
                dlst=[self.env['ALIAS']]+dlst
            #print dlst
            for d in dlst:
                tenv=def_env['PART_INFO'][d]['ENV']
                #plist=mappers.sub_lst(self.env,["${PARTS('"+d+"','LIBPATH')}"],def_env)
                plist=mappers.sub_lst(self.env,tenv['LIBPATH'],def_env)
                for p in plist:
                    rp='-Wl,-rpath-link='+self.env.Dir(p).path
                    if rp not in rplst:
                        rplst.append(rp)
                        #print ' \t',rp
            rplst=common.make_unique(rplst)
            self.env.Replace(LINKFLAGS=rplst)
            #print 'LINKFLAGS LIST',self.env['LINKFLAGS']


class map_rpath_part:
    '''This class adds to the RPATH value based on location of where there .SO
    are stored.. classically in a seperate OUT_LIB directory. This allow for correct
    running of the program after a build without special setup'''
    def __init__(self,env,add_self=False):
        self.env=env
        self.add_self=add_self
    def __call__(self):
        if common.g_args['AUTO_RPATH']==True:
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
                plist=mappers.sub_lst(self.env,["${PARTS('"+val+"','LIBPATH')}"],def_env)
                for p in plist:
                    r=self.env.Literal('\'$$ORIGIN/'+common.relpath(self.env.Dir(p).path,self.env.Dir('$OUT_BIN').path)+'\'')
                    #r=relpath(self.env.Dir(p).path,self.env.Dir('$OUT_BIN').path)
                    if r not in rlst:
                        rlst.append(r)
                        #print ' \t',r
            rlst=common.make_unique_str(rlst)
            self.env.Replace(RPATH=rlst)
            #print 'RPATH LIST',self.env['RPATH']
          
# add configuartion varaible
common.add_config_var('AUTO_RPATH',True)
