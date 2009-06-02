
import os
import common
import SCons.Script 
import version


def sub_lst(env,lst,def_env={"PARTS_COMPLEX_SUB":0}):
    ''' Utility function to help with returning list from env.subst() as this function
    doesn't like the returning of lists. This returns a list seperated by the binary value of 1
    which is not used as a normal printing character.'''
    ret=[]
    def_env["PARTS_COMPLEX_SUB"]=def_env["PARTS_COMPLEX_SUB"]+1
    for i in lst:
        v=env.subst(str(i)).split("\1")
        ret.extend(v)
    def_env["PARTS_COMPLEX_SUB"]=def_env["PARTS_COMPLEX_SUB"]-1
    return common.make_unique(ret)

def find_matching_version(def_env,env,id,ver_range,alias_lst):
    ''' this function is used by the part_ID_mapper to help find the lastest 
    version number of a given part. It was pulled out as a seperate function to 
    mainly to help the readbility of the rather large partID mapper function'''
    
    pinfo=None
    ret=None
    last_ver=None
    arch=env['TARGET_SYSTEM'].Architecture
    rpt=def_env['PARTS_REPORTER']
    try:
        for i in alias_lst[id]:
            if def_env['PART_INFO'].has_key(i) == False:
                rpt.part_warning(env,"Default Env doesn't have key"+i)
            pinfo=def_env['PART_INFO'][i]
            if pinfo['NAME'] == id:
                # get the version info
                tmp=pinfo['VERSION']
                #if this is a string we need subst it to get real version
                if common.is_string(tmp):
                    this_ver=version.version(env.subst(tmp))
                else:
                    # else we assume this is a version object
                    this_ver=tmp
                
                if this_ver in ver_range and this_ver > last_ver and arch==pinfo['ENV']['TARGET_SYSTEM'].Architecture:
                    last_ver=this_ver
                    ret=pinfo
                            
    except Exception:
        rpt.part_error(env,"Error in alias look up\nID->Alias map "+str(alias_lst)+'\nlooking up ['+id+'] with version range ['+str(ver_range)+']')
        env.Exit(0)
    return ret

class part_mapper:
    ''' This class maps the part vars in the Default enviroment to the actual 
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part alias. It has to do a small hack to 
    replace a the property in the actual Env else a SCons issue with subst and lists
    causes the subst to fail.
    '''
    name='PARTS'
    def __init__(self,part_name,part_prop,ignore=False):
        self.part_name = part_name
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            rpt=def_env['PARTS_REPORTER']
            pinfo = def_env['PART_INFO'].get(self.part_name,None)
            if pinfo == None:
                rpt.part_warning(env,self.name+" mapper: Part "+self.part_name+" was not defined")
                return ''
            ret=pinfo.get(self.part_prop,None)
            if ret== None:
                if pinfo.has_key(self.part_prop)==False and self.ignore==False:
                    rpt.part_warning(env,self.name+" mapper: Property "+self.part_name+'.'+self.part_prop+" was not defined")
                return ''
            penv=pinfo['ENV']
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,def_env)
                pinfo[self.part_prop]=ret
                if def_env["PARTS_COMPLEX_SUB"]==0:
                    #print "before PARTS()",env[self.part_prop],ret
                    idx=env[self.part_prop].index("${"+self.name+"('"+self.part_name+"','"+self.part_prop+"')}")
                    if common.is_list(env[self.part_prop]):
                        env[self.part_prop][idx:idx+1]=ret
                    else:
                        env[self.part_prop]=[ret]
                    #print "after PARTS()",env[self.part_prop]
                    if ret == []:
                        return ""
                    else:
                        return ret[0]
                else:
                    return "\1".join(ret)
            else:
                return penv.subst(str(ret))
            
        except Exception,ec:
            import traceback,StringIO
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            rpt.part_error(env,"Exception in PARTS mapping happened\n"+ec_str.getvalue())
            env.Exit(0)
        return ret

#already_printed = set()

class part_id_mapper:
    ''' This class maps the part name and version range to the correct alias in 
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias. 
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name='PARTID'
    def __init__(self,id,ver_range,part_prop,ignore=False):
        self.part_id = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            #print "PARTID resolving","${PARTID('"+self.part_id+"','"+str(self.ver_range)+"','"+self.part_prop+"')}"
            def_env=SCons.Script.DefaultEnvironment()
            rpt=def_env['PARTS_REPORTER']
            this_pinfo=def_env['PART_INFO'][env['ALIAS']]
            #first we need to get the id to alias map
            id_to_alias = def_env.get('PART_IDS',{})
            if self.part_id not in id_to_alias:
                if common.g_args["PARTS_MODE"]=='build':
                    rpt.part_warning(env,self.name+" Did not find Part name ["+self.part_id+"] in name->alias dictionary",True)
                return ''
            
            #Find matching verion pinfo
            pinfo=find_matching_version(def_env,env,self.part_id,self.ver_range,id_to_alias)
                
            if pinfo == None:
                rpt.part_error(env,self.name+": Part name ["+self.part_id+"] did not define version that matches version range of ["+str(self.ver_range)+"] for "+env['ARCHITECTURE']+" ARCHITECTURE")
                exit(0)
            
            ret=pinfo.get(self.part_prop,None)
            if ret== None:
                if self.ignore==False:
                    rpt.part_error(env,self.name+": Error -- Property"+pinfo["ALIAS"]+'.'+self.part_prop+"was not defined")
                    env.Exit(0)
                else:
                    ret= ""
                
                            
            penv=pinfo['ENV']
            if common.is_list(ret):
                
                if len(ret)>1:
                    ret=sub_lst(penv,ret,def_env)
                
                pinfo[self.part_prop]=ret
                if def_env["PARTS_COMPLEX_SUB"]==0:
                    key="${"+self.name+"('"+self.part_id+"','"+str(self.ver_range)+"','"+self.part_prop
                    if self.ignore==False:
                        key=key+"')}"
                    else:
                        key=key+"',True)}"
                    
                    #print "before PARTID()",env[self.part_prop],ret,key
                    idx=env[self.part_prop].index(key)
                    env[self.part_prop][idx:idx+1]=ret
                    #print "after PARTID()",env[self.part_prop]
                    if ret == []:
                        #print "PARTID resolving -- Done 1a",ret
                        return ""
                    else:
                        #print "PARTID resolving -- Done 1b",ret[0]
                        return ret[0]
                else:
                    #print "PARTID resolving -- Done 2","\1".join(ret)
                    return "\1".join(ret)
            else:
                #print "PARTID resolving -- Done 3",penv.subst(str(ret))
                return penv.subst(str(ret))
        except Exception,ec:
            import traceback,StringIO
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            rpt.part_error(env,"Exception in PARTID mapping happened\n"+ec_str.getvalue())
            env.Exit(0)
        #print "PARTID resolving -- Done 4",ret
        return ret
class part_subst_mapper:
    ''' This class maps the part vars in the Default enviroment to the actual 
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part alias. This version doesn't have the 
    small hack to fix the list subst in SCons. As such it a bit faster is is mostly 
    used for delay substiution of more simple value such as $OUT_BIN which may contain
    values not fully filled in.
    '''
    name='PARTSUB'
    def __init__(self,part_name,part_prop):
        self.part_name = part_name
        self.part_prop = part_prop

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            rpt=def_env['PARTS_REPORTER']
            pinfo = def_env['PART_INFO'].get(self.part_name,None)
            if pinfo == None:
                rpt.part_warning(env,"PARTSUB Alias "+self.part_name+" was not defined")
                return 'None'
            penv=pinfo['ENV']
            ret = penv.subst(self.part_prop)
            #print 'PARTS: Verbose -- PARTSUB MAPPED',"#${PARTSUB('"+self.part_name+"','"+self.part_prop+"')} to",ret
        except Exception,ec:
            rpt.part_error(env,"Some exception in "+self.name+" mapping happened")
            rpt.part_message(str(ec))
            env.Exit(0)
        return ret
    
class part_name_mapper:
    ''' Allows for an easy fallback mapping between the part alias and name'''
    name='PARTNAME'
    def __init__(self,part_alias):
        self.part_alias = part_alias

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            rpt=def_env['PARTS_REPORTER']
            pinfo = def_env['PART_INFO'].get(self.part_alias,None)
            if pinfo == None:
                rpt.part_warning(env,"PARTNAME Alias "+ self.part_alias+" was not defined")
                return 'None'
            if pinfo['NAME']==None:
                ret=pinfo['ALIAS']
            else:
                ret=pinfo['NAME']
        except Exception,ec:
            import traceback,StringIO
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            rpt.part_error(env,"Exception in "+self.name+" mapping happened\n"+ec_str.getvalue())
            env.Exit(0)
        return ret

class part_shortname_mapper:
    '''
    Allows for an easy fallback mapping between the part short alias 
    and short name
    '''
    name='PARTSHORTNAME'
    def __init__(self,part_name):
        self.part_name = part_name

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            rpt=def_env['PARTS_REPORTER']
            pinfo = def_env['PART_INFO'].get(self.part_name,None)
            if pinfo == None:
                rpt.part_warning(env,"PARTSHORTNAME Alias " + self.part_name+" was not defined")
                return 'None'
            if pinfo['SHORT_NAME']==None:
                ret=pinfo['SHORT_ALIAS']
            else:
                ret=pinfo['SHORT_NAME']
        except Exception,ec:
            import traceback,StringIO
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            rpt.part_error(env,"Exception in "+self.name+" mapping happened\n"+ec_str.getvalue())
            env.Exit(0)
        return ret

class abspath_mapper:
    ''' Allows for an easy expanding value as directory or files'''
    name='ABSPATH'
    def __init__(self,value):
        self.value = value

    def __call__(self, target, source, env, for_signature):
        if self.value[0] == '$':
            return env.Entry(env.subst(self.value)).abspath
        return env.Entry(env.subst("${"+self.value+"}")).abspath

class relpath_mapper:
    ''' allows one to define a relative path'''
    name='RELPATH'
    def __init__(self,_to,_from):
        self._to = _to
        self._from = _from

    def __call__(self, target, source, env, for_signature):
        if self._to[0] == '$':
            t = env.Entry(env.subst(self._to)).abspath
        t = env.Entry(env.subst("${"+self._to+"}")).abspath
        if self._from[0] == '$':
            f = env.Entry(env.subst(self._from)).abspath
        f = env.Entry(env.subst("${"+self._from+"}")).abspath
        return common.relpath(t,f)+os.sep
    

common.add_mapper(part_mapper)
common.add_mapper(part_id_mapper)
common.add_mapper(part_subst_mapper)
common.add_mapper(part_name_mapper)
common.add_mapper(part_shortname_mapper)
common.add_mapper(abspath_mapper)
common.add_mapper(relpath_mapper)
