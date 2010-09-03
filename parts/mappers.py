import thread
import os
import common
import SCons.Script 
import version
import reporter
import SCons.Script.Main
import traceback
import StringIO

g_complex_sub={}

class mapper(object):
    def __init__(self):
        self.stackframe=reporter.GetPartStackFrameInfo()
        
    def alias_missing(self,env):
        if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):                
            
            reporter.report_warning(self.name,"Alias", self.part_alias,"was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe
                )
        else:
            reporter.report_error(
                self.name+" Alias",self.part_alias,"was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
    def name_to_alias_failed(self,env):
        found_data=''
        name_to_alias=common.g_engine._part_manager._alias_list(self.name)
        for a in name_to_alias:
            tmp=common.g_engine._part_manager._from_alias(a)
            found_data+=" Alias=%s, version=%s, matching platforms=%s\n"%(tmp.Alias,tmp.Version,tmp._platform_match)
        if found_data=='':
            found_data=" Nothing was found"
            
        reporter.report_error(
            self.name+": Part name <%s> did not define version that matches version range of <%s> for %s architechture\n Found:\n%s"%\
            (self.part_name,str(self.ver_range),env['TARGET_PLATFORM'].ARCH,found_data),
            "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
            (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
            stackframe=self.stackframe,
            exit=False
            )
        #because the exceptionthrown will not get threw the try catch in subst()
        env.Exit(1)
        
    def unexpected_error(self,env):
        ec_str=StringIO.StringIO()
        traceback.print_exc(file=ec_str)
        reporter.report_error(
            "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
            stackframe=self.stackframe,
            exit=False
            )
        #because the exceptionthrown will not get threw the try catch in subst()
        env.Exit(1)


def sub_lst(env,lst,thread_id):
    ''' Utility function to help with returning list from env.subst() as this function
    doesn't like the returning of lists. This returns a list seperated by the binary value of 1
    which is not used as a normal printing character.'''
    ret=[]
    g_complex_sub[thread_id]=g_complex_sub[thread_id]+1
    for i in lst:
        v=env.subst(str(i)).split("\1")
        #ret.extend(v)
        ret=common.extend_unique(ret,v)
    g_complex_sub[thread_id]=g_complex_sub[thread_id]-1
    return ret#common.make_unique(ret)


class part_mapper(mapper):
    ''' This class maps the part property in the Part object. It then returns the value
    of the property for the requested part alias. It has to do a small hack to 
    replace a the property in the actual Env else a SCons issue with subst and lists
    causes the subst to fail.
    '''
    name='PARTS'
    def __init__(self,alias,prop,ignore=False):
        mapper.__init__(self)
        self.part_alias = alias
        self.part_prop = prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            thread_id=thread.get_ident() 
            if thread_id not in g_complex_sub:
                g_complex_sub[thread_id] = 0
            reporter.verbose_msg(['parts_mappers'],"Getting part object for alias:",self.part_alias)
                
            pobj=common.g_engine._part_manager._from_alias(self.part_alias)
            if pobj is None:
                self.alias_missing(env)
                return ''
            
            ret=getattr(pobj,self.part_prop,None)
            if ret is None:
                if self.ignore==False:
                    reporter.report_warning(self.name,"mapper: Property ",
                        self.part_alias+'.'+self.part_prop," was not defined",
                        stackframe=self.stackframe
                        )
                return ''
            reporter.verbose_msg(['parts_mappers'],'Property %s = "%s" for part alias "%s"'%(self.part_prop,ret,self.part_alias))
            penv=pobj.Env
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                
                setattr(pobj,self.part_prop,ret)
                if g_complex_sub[thread_id]==0:
                    reporter.verbose_msg(['parts_mappers'],"before PARTS()",env[self.part_prop],ret)
                    idx=env[self.part_prop].index("${"+self.name+"('"+self.part_alias+"','"+self.part_prop+"')}")
                    if common.is_list(env[self.part_prop]):
                        env[self.part_prop][idx:idx+1]=ret
                    else:
                        env[self.part_prop]=[ret]
                    reporter.verbose_msg(['parts_mappers'], "after PARTS()",env[self.part_prop])
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
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
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
        self.part_name = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop.lower()
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            
            #Find matching verion pinfo
            pobj=common.g_engine._part_manager._from_nvp(
                self.part_name,
                self.ver_range,
                env['TARGET_PLATFORM']
            )
                        
            if pobj is None:
                self.name_to_alias_failed(env)
            
            ret=getattr(pobj,self.part_prop,None)
            if ret is None:
                if self.ignore==False:
                    reporter.report_warning(self.name,"mapper: Property ",
                        pobj.Alias+'.'+self.part_prop," was not defined",
                        stackframe=self.stackframe
                        )
                return ''
            reporter.verbose_msg(['partid_mapper'],'Property %s = "%s" for part alias "%s"'%(self.part_prop,ret,pobj.Alias))
            penv=pobj.Env

            thread_id=thread.get_ident() 
            if thread_id not in g_complex_sub:
                g_complex_sub[thread_id] = 0
                
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                #setattr(pobj,self.part_prop,ret)
                if g_complex_sub[thread_id]==0:
                    reporter.verbose_msg(['partid_mapper'],"before",self.name,env[self.part_prop],ret)
                    if self.ignore == True:
                        idx=env[self.part_prop].index("${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"',True)}")
                    else:
                        idx=env[self.part_prop].index("${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"')}")
                    if common.is_list(env[self.part_prop]):
                        env[self.part_prop][0:idx+1]=common.extend_if_absent(env[self.part_prop][0:idx],ret)
                    else:
                        env[self.part_prop]=[ret]
                    reporter.verbose_msg(['partid_mapper'], "after",self.name,env[self.part_prop])
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
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
        return ret

class part_id_export_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in 
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias. 
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name='PARTIDEXPORTS'
    def __init__(self,id,ver_range,part_prop,ignore=False):
        mapper.__init__(self)
        self.part_name = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            pobj_org=common.g_engine._part_manager._from_env(env)
           #Find matching verion pinfo
            pobj=common.g_engine._part_manager._from_nvp(
                self.part_name,
                self.ver_range,
                env['TARGET_PLATFORM']
            )
                        
            if pobj is None:
                self.name_to_alias_failed(env)
            
            ret=pobj._exports.get(self.part_prop,[])
            
            reporter.verbose_msg(['partexport_mapper'],'Property %s = "%s" for part alias "%s"'%(self.part_prop,ret,pobj.Alias))
            penv=pobj.Env

            thread_id=thread.get_ident() 
            if thread_id not in g_complex_sub:
                g_complex_sub[thread_id] = 0
                
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                    pobj._exports[self.part_prop]=ret
                if g_complex_sub[thread_id]==0:
                    
                    if self.ignore == True:
                        str_val="${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"',True)}"
                        
                    else:
                        str_val="${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"')}"
                    
                    try:
                        # set the value in the exports to prevent recusive hitting of this again latter
                        # value might not exist in cases of programs or components that are on the top 
                        # of the tree.. so if we get a KeyError we can ignore it
                        idx=pobj_org._exports[self.part_prop].index(str_val)
                        pobj_org._exports[self.part_prop][idx:idx+1]=ret
                    except KeyError:
                        pass
                    except ValueError:
                        pass
                    try:
                        reporter.verbose_msg(['partexport_mapper'],"before",self.name,env[self.part_prop],ret)
                        idx=env[self.part_prop].index(str_val)
                        if common.is_list(env[self.part_prop]):
                            env[self.part_prop][0:idx+1]=common.extend_if_absent(env[self.part_prop][0:idx],ret)
                        else:
                            env[self.part_prop]=[ret]
                        reporter.verbose_msg(['partexport_mapper'], "after",self.name,env[self.part_prop])
                    except KeyError, e:
                        reporter.verbose_msg(['partexport_mapper'], "KeyError",e)
                    except ValueError:
                        pass
                    
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
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
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
        self.part_name = id
        self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.ignore=ignore

    def __call__(self, target, source, env, for_signature):
        try:
            pobj_org=common.g_engine._part_manager._from_env(env)
            #Find matching verion pinfo
            pobj=common.g_engine._part_manager._from_nvp(
                self.part_name,
                self.ver_range,
                env['TARGET_PLATFORM']
            )
            if pobj is None:
                self.name_to_alias_failed(env)
            
            ret=pobj._exports.get(self.part_prop,[])
            
            reporter.verbose_msg(['partlib_mapper'],'Property %s = "%s" for part name "%s"'%(self.part_prop,ret,pobj.Name))
            penv=pobj.Env

            thread_id=thread.get_ident() 
            if thread_id not in g_complex_sub:
                g_complex_sub[thread_id] = 0
                
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                pobj._exports[self.part_prop]=ret
                if g_complex_sub[thread_id]==0:
                    if self.ignore == True:
                        str_val="${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"',True)}"
                        
                    else:
                        str_val="${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"')}"
                    
                    try:
                        # set the value in the exports to prevent recusive hitting of this again latter
                        # value might not exist in cases of programs or components that are on the top 
                        # of the tree.. so if we get a KeyError we can ignore it
                        idx=pobj_org._exports[self.part_prop].index(str_val)
                        pobj_org._exports[self.part_prop][idx:idx+1]=ret
                    except KeyError:
                        pass
                    except ValueError:
                        pass                    
                        
                    try:
                        reporter.verbose_msg(['partlib_mapper'],"before",self.name,env[self.part_prop],ret)
                        idx=env[self.part_prop].index(str_val)
                        if common.is_list(env[self.part_prop]):
                            env[self.part_prop][0:idx+1]=common.extend_unique(env[self.part_prop][0:idx],ret)
                        else:
                            env[self.part_prop]=[ret]
                        reporter.verbose_msg(['partlib_mapper'], "after",self.name,env[self.part_prop])
                    except KeyError, e:
                        reporter.verbose_msg(['partlib_mapper'], "KeyError",e)
                    except ValueError:
                        pass
                        
                    
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
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exceptionthrown will not get threw the try catch in subst()
            env.Exit(1)
            
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
    def __init__(self,part_alias,substr):
        mapper.__init__(self)
        self.part_alias = part_alias
        self.substr = substr

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            
            pobj = common.g_engine._part_manager._from_alias(self.part_alias)
            if pobj is None:
                self.alias_missing(env)
                return None
            penv=pobj.Env
            ret = penv.subst(self.substr)
            #print 'PARTS: Verbose -- PARTSUB MAPPED',"#${PARTSUB('"+self.part_name+"','"+self.part_prop+"')} to",ret
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
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
            pobj=common.g_engine._part_manager._from_alias(self.part_alias)
            try:
                ret=pobj.Name
            except AttributeError: 
                self.alias_missing(env)
                return None
            
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
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
    def __init__(self,part_alias):
        mapper.__init__(self)
        self.part_alias = part_alias

    def __call__(self, target, source, env, for_signature):
        try:
            pobj=common.g_engine._part_manager._from_alias(self.part_alias)
            
            if pobj is None:
                self.alias_missing(env)
                return None
                
            ret=pobj.ShortName
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            reporter.report_error(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
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
common.add_mapper(part_id_export_mapper)
common.add_mapper(part_subst_mapper)
common.add_mapper(part_name_mapper)
common.add_mapper(part_shortname_mapper)
common.add_mapper(abspath_mapper)
common.add_mapper(relpath_mapper)
common.add_mapper(part_lib_mapper)

common.AddBoolVariable('MAPPER_BAD_ALIAS_AS_WARNING',True,'Controls if a missing alias is an error or a warning')
