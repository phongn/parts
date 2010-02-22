
import os
import common
import SCons.Script 
import version
import reporter
import SCons.Script.Main
import traceback
import StringIO


class mapper(object):
    def __init__(self):
        self.stackframe=reporter.GetPartStackFrameInfo()



def sub_lst(env,lst,def_env={"PARTS_COMPLEX_SUB":0}):
    ''' Utility function to help with returning list from env.subst() as this function
    doesn't like the returning of lists. This returns a list seperated by the binary value of 1
    which is not used as a normal printing character.'''
    ret=[]
    def_env["PARTS_COMPLEX_SUB"]=def_env["PARTS_COMPLEX_SUB"]+1
    for i in lst:
        v=env.subst(str(i)).split("\1")
        #ret.extend(v)
        ret=common.extend_unique(ret,v)
    def_env["PARTS_COMPLEX_SUB"]=def_env["PARTS_COMPLEX_SUB"]-1
    return ret#common.make_unique(ret)

def find_matching_version(def_env,env,id,ver_range,alias_lst):
    ''' this function is used by the part_ID_mapper to help find the lastest 
    version number of a given part. It was pulled out as a seperate function to 
    mainly to help the readbility of the rather large partID mapper function'''
    
    pinfo=None
    ret=None
    last_ver=None
    arch=env['TARGET_PLATFORM']
    
    try:
        for i in alias_lst[id]:
            if def_env['PART_INFO'].has_key(i) == False:
                reporter.report_error(
                    "Default Env doesn't have key",i,
                    exit=False
                    )
                #because the exceptionthrown will not get threw the try catch in subst()
                env.Exit(1)
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
                    
                if this_ver in ver_range and this_ver > last_ver and arch==pinfo['PLATFORM_MATCH']:
                    last_ver=this_ver
                    ret=pinfo
                            
    except Exception, ec:
        #print type(ec),ec
        reporter.report_error(
            "Looking up Name <%s> in Name->Alias map %s\n version range <%s>\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
            (id,str(alias_lst),str(ver_range),env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
            exit=False
            )
        #because the exceptionthrown will not get threw the try catch in subst()
        env.Exit(1)
    return ret

class part_mapper(mapper):
    ''' This class maps the part vars in the Default enviroment to the actual 
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part alias. It has to do a small hack to 
    replace a the property in the actual Env else a SCons issue with subst and lists
    causes the subst to fail.
    '''
    name='PARTS'
    def __init__(self,part_name,part_prop,ignore=False):
        mapper.__init__(self)
        self.part_name = part_name
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            
            pinfo = def_env['PART_INFO'].get(self.part_name,None)
            if pinfo == None:
                if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):
                    
                    reporter.report_warning(self.name,"mapper: Part",self.part_name,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe)
                else:
                    reporter.report_error(
                        self.name,"mapper: Part",self.part_name,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe,
                        exit=False
                        )
                    #because the exceptionthrown will not get threw the try catch in subst()
                    env.Exit(1)
                return ''
            ret=pinfo.get(self.part_prop,None)
            if ret== None:
                if pinfo.has_key(self.part_prop)==False and self.ignore==False:
                    reporter.report_warning(self.name,"mapper: Property ",
                        self.part_name+'.'+self.part_prop," was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe
                        )
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
            
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
        return ret

#already_printed = set()

class part_id_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in 
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias. 
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name='PARTID'
    def __init__(self,id,ver_range,part_prop,ignore=False):
        mapper.__init__(self)
        self.part_id = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            #print "PARTID resolving","${PARTID('"+self.part_id+"','"+str(self.ver_range)+"','"+self.part_prop+"')}"
            def_env=SCons.Script.DefaultEnvironment()
            
            this_pinfo=def_env['PART_INFO'][env['ALIAS']]
            #first we need to get the id to alias map
            id_to_alias = def_env.get('PART_IDS',{})     
            
            if self.part_id not in id_to_alias:
                if env["PARTS_MODE"]=='build':
                    if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):
                        reporter.report_warning(self.name,
                            "Did not find Part name <%s> in internal name->alias dictionary"%(self.part_id),
                            "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                            (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                            print_once=True,
                            stackframe=self.stackframe
                            )
                    else:
                        reporter.report_error(
                            self.name,"Did not find Part name <"+self.part_id+"> in name->alias dictionary",
                            "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                            (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                            stackframe=self.stackframe,
                            exit=False
                            )                        
                        #because the exceptionthrown will not get threw the try catch in subst()
                        env.Exit(1)
                        
                return ''
            
            #Find matching verion pinfo
            pinfo=find_matching_version(def_env,env,self.part_id,self.ver_range,id_to_alias)
            
            if pinfo == None:
                reporter.report_error(
                    self.name+": Part name <%s> did not define version that matches version range of <%s> for %s ARCHITECTURE"%\
                    (self.part_id,str(self.ver_range),env['TARGET_PLATFORM'].ARCH),
                    "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                    (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                    stackframe=self.stackframe,
                    exit=False
                    )
                #because the exceptionthrown will not get threw the try catch in subst()
                env.Exit(1)
                
            
            ret=pinfo.get(self.part_prop,None)
            if ret== None:
                if self.ignore==False:
                    reporter.report_error(
                        self.name+": Property",pinfo["ALIAS"]+'.'+self.part_prop,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe,
                        exit=False
                        )
                    #because the exceptionthrown will not get threw the try catch in subst()
                    env.Exit(1)
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
                    #env[self.part_prop][idx:idx+1]=ret
                    env[self.part_prop][0:idx+1]=common.extend_if_absent(env[self.part_prop][0:idx],ret)#ret                    
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
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
        #print "PARTID resolving -- Done 4",ret
        return ret

class part_lib_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in 
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias. 
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name='PARTLIB'
    def __init__(self,id,ver_range,part_prop,ignore=False):
        mapper.__init__(self)
        self.part_id = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            #print "PARTID resolving","${PARTID('"+self.part_id+"','"+str(self.ver_range)+"','"+self.part_prop+"')}"
            def_env=SCons.Script.DefaultEnvironment()
            
            this_pinfo=def_env['PART_INFO'][env['ALIAS']]
            #first we need to get the id to alias map
            id_to_alias = def_env.get('PART_IDS',{})     
            
            if self.part_id not in id_to_alias:
                if env["PARTS_MODE"]=='build':
                    if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):
                        reporter.report_warning(self.name,
                            "Did not find Part name <%s> in internal name->alias dictionary"%(self.part_id),
                            "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                            (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                            print_once=True,
                            stackframe=self.stackframe
                            )
                    else:
                        reporter.report_error(
                            self.name,"Did not find Part name <"+self.part_id+"> in name->alias dictionary",
                            "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                            (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                            stackframe=self.stackframe,
                            exit=False
                            )                        
                        #because the exceptionthrown will not get threw the try catch in subst()
                        env.Exit(1)
                        
                return ''
            
            #Find matching verion pinfo
            pinfo=find_matching_version(def_env,env,self.part_id,self.ver_range,id_to_alias)
            
            if pinfo == None:
                reporter.report_error(
                    self.name+": Part name <%s> did not define version that matches version range of <%s> for %s ARCHITECTURE"%\
                    (self.part_id,str(self.ver_range),env['TARGET_PLATFORM'].ARCH),
                    "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                    (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                    stackframe=self.stackframe,
                    exit=False
                    )
                #because the exceptionthrown will not get threw the try catch in subst()
                env.Exit(1)
                
            
            ret=pinfo.get(self.part_prop,None)
            if ret== None:
                if self.ignore==False:
                    reporter.report_error(
                        self.name+": Property",pinfo["ALIAS"]+'.'+self.part_prop,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe,
                        exit=False
                        )
                    #because the exceptionthrown will not get threw the try catch in subst()
                    env.Exit(1)
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
                    #env[self.part_prop][idx:idx+1]=ret
                    env[self.part_prop][0:idx+1] = common.extend_unique(env[self.part_prop][0:idx],ret) # Pratim says : I am not sure why LHS has idx+1                   
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
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
        #print "PARTID resolving -- Done 4",ret
        return ret

class part_subst_mapper(mapper):
    ''' This class maps the part vars in the Default enviroment to the actual 
    value stored the in default Env PART_INFO map. It then returns the value
    of the property for the requested part alias. This version doesn't have the 
    small hack to fix the list subst in SCons. As such it a bit faster is is mostly 
    used for delay substiution of more simple value such as $OUT_BIN which may contain
    values not fully filled in.
    '''
    name='PARTSUB'
    def __init__(self,part_name,part_prop):
        mapper.__init__(self)
        self.part_name = part_name
        self.part_prop = part_prop

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            
            pinfo = def_env['PART_INFO'].get(self.part_name,None)
            if pinfo == None:
                if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):
                    
                    reporter.report_warning(self.name,"Alias",self.part_name,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe
                        )
                else:
                    reporter.report_error(
                        self.name+" Alias "+self.part_name+" was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe,
                        exit=False
                        )
                    #because the exceptionthrown will not get threw the try catch in subst()
                    env.Exit(1)
                return 'None'
            penv=pinfo['ENV']
            ret = penv.subst(self.part_prop)
            #print 'PARTS: Verbose -- PARTSUB MAPPED',"#${PARTSUB('"+self.part_name+"','"+self.part_prop+"')} to",ret
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
        return ret
    
class part_name_mapper(mapper):
    ''' Allows for an easy fallback mapping between the part alias and name'''
    name='PARTNAME'
    def __init__(self,part_alias):
        mapper.__init__(self)
        self.part_alias = part_alias

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            
            pinfo = def_env['PART_INFO'].get(self.part_alias,None)
            if pinfo == None:
                if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):
                    
                    reporter.report_warning(self.name,"Alias",self.part_alias,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe)
                else:
                    reporter.report_error(
                        self.name+" Alias "+ self.part_alias+" was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe,
                        exit=False
                        )
                    #because the exceptionthrown will not get threw the try catch in subst()
                    env.Exit(1)
                return 'None'
            if pinfo['NAME']==None:
                ret=pinfo['ALIAS']
            else:
                ret=pinfo['NAME']
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
        return ret

class part_shortname_mapper(mapper):
    '''
    Allows for an easy fallback mapping between the part short alias 
    and short name
    '''
    name='PARTSHORTNAME'
    def __init__(self,part_name):
        mapper.__init__(self)
        self.part_name = part_name

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            
            pinfo = def_env['PART_INFO'].get(self.part_name,None)
            if pinfo == None:
                if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):                
                    
                    reporter.report_warning(self.name,"Alias", self.part_alias,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe
                        )
                else:
                    reporter.report_error(
                        self.name+" Alias",self.part_name,"was not defined",
                        "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                        (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                        stackframe=self.stackframe,
                        exit=False
                        )
                    #because the exceptionthrown will not get threw the try catch in subst()
                    env.Exit(1)
                    
                return 'None'
            if pinfo['SHORT_NAME']==None:
                ret=pinfo['SHORT_ALIAS']
            else:
                ret=pinfo['SHORT_NAME']
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
        return ret

class abspath_mapper(mapper):
    ''' Allows for an easy expanding value as directory or files'''
    name='ABSPATH'
    def __init__(self,value):
        mapper.__init__(self)
        self.value = value

    def __call__(self, target, source, env, for_signature):
        if self.value[0] == '$':
            return env.Entry(env.subst(self.value)).abspath
        return env.Entry(env.subst("${"+self.value+"}")).abspath

class relpath_mapper(mapper):
    ''' allows one to define a relative path'''
    name='RELPATH'
    def __init__(self,_to,_from):
        mapper.__init__(self)
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
common.add_mapper(part_lib_mapper)

common.AddBoolVariable('MAPPER_BAD_ALIAS_AS_WARNING',True,'Controls if a missing alias is an error or a warning')
