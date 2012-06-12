import glb
import part_ref
import policy as Policy
import common
import version
import api.output
import errors
import target_type

import SCons.Script.Main
import SCons.Script 
import SCons.Subst

import StringIO
import traceback
import thread
import os

g_complex_sub={}

class mapper(object):
    def __init__(self):
        self.stackframe=errors.GetPartStackFrameInfo()
        
    def alias_missing(self,env):
        if env.get('MAPPER_BAD_ALIAS_AS_WARNING',True):                
            
            api.output.warning_msg(self.name,"Alias", self.part_alias,"was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe
                )
        else:
            api.output.error_msg(
                self.name+" Alias",self.part_alias,"was not defined",
                "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
                (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
            env.Exit(1)
            
    # old function to remove when it is safe
    def nvp_to_alias_failed(self,env,policy=Policy.ReportingPolicy.warning):
        found_data=''
        name_to_alias=glb.engine._part_manager._alias_list(self.name)
        for a in name_to_alias:
            tmp=glb.engine._part_manager._from_alias(a)
            found_data+=" Alias=%s, version=%s, matching platforms=%s\n"%(tmp.Alias,tmp.Version,tmp._platform_match)
        if found_data=='':
            found_data=" Nothing was found"
        
        api.output.policy_msg(
            Policy.ReportingPolicy.error,#policy,
            [self.name,'mappers'],
            self.name+": Part name <%s> did not define version that matches version range of <%s> for %s architechture\n Found:\n%s"%\
            (self.part_name,str(self.ver_range),env['TARGET_PLATFORM'].ARCH,found_data),
            "\n For Part name <%s> Version <%s> for TARGET_PLATFORM <%s>"%\
            (env.PartName(),env.PartVersion(),env['TARGET_PLATFORM']),
            stackframe=self.stackframe,
            exit=False
            )
        #because the exception thrown will not get thrown the try catch in subst()
        env.Exit(1)
        
    def name_to_alias_failed(self,env,match,policy=Policy.ReportingPolicy.error):
        
        if match.hasAmbiguousMatch:
            reason=match.AmbiguousMatchStr()
        else:
            reason=match.NoMatchStr() 
        api.output.policy_msg(
            Policy.ReportingPolicy.error,
            [self.name,'mappers'],
            "Failed to map dependency for {0}\n  with Version: {1} config: {2} TARGET_PLATFORM: {3}\n {4}".format(env.PartName(),env.PartVersion(),env['CONFIG'],env['TARGET_PLATFORM'],reason),
            stackframe=self.stackframe,
            exit=False
            )
        #because the exception thrown will not get thrown the try catch in subst()
        env.Exit(1)
        
    def unexpected_error(self,env):
        ec_str=StringIO.StringIO()
        traceback.print_exc(file=ec_str)
        api.output.error_msg(
            "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
            stackframe=self.stackframe,
            exit=False
            )
        #because the exception thrown will not get thrown the try catch in subst()
        env.Exit(1)


def sub_lst(env,lst,thread_id):
    ''' Utility function to help with returning list from env.subst() as this function
    doesn't like the returning of lists. This returns a list seperated by the binary value of 1
    which is not used as a normal printing character.'''
    ret=[]
    g_complex_sub[thread_id]=g_complex_sub.get(thread_id,0)+1
    spacer="."*(g_complex_sub[thread_id]-1)
    api.output.trace_msg(['sub_lst','mapper'],spacer,"sub_lst getting value for",lst)
    for i in lst:
        root=env.Dir("#")
        if isinstance(i,SCons.Node.FS.Base) and i.is_under(root):
                v=[root.rel_path(i)]
        else:
            v=env.subst(str(i)).split("\1")
        #ret.extend(v)
        ret=common.extend_unique(ret,v)
    api.output.trace_msg(['sub_lst','mapper'],spacer,"sub_lst returning",ret)
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
            try:
                spacer="."*g_complex_sub[thread_id]
            except KeyError:
                g_complex_sub[thread_id] = 0
                spacer="."*g_complex_sub[thread_id]
            
            api.output.trace_msg(['parts_mapper','mapper'],spacer,'Expanding value "${{{0}("{1}","{2}",{3})}}"'.format(self.name,self.part_alias,self.part_prop,self.ignore))
                
            pobj=glb.engine._part_manager._from_alias(self.part_alias)
            if pobj is None:
                api.output.trace_msg(['parts_mapper','mapper'],spacer,'Failed to find Part with Alias: {0}'.format(self.part_alias))
                self.alias_missing(env)
                return ''
            api.output.trace_msg(['parts_mapper','mapper'],spacer,'Found Part with Alias: {0}'.format(self.part_alias))
            ret=getattr(pobj,self.part_prop,None)
            if ret is None:
                tmp=self.part_prop[0]+self.part_prop[1:].lower()
                ret=getattr(pobj,tmp,None)
            if ret is None:
                if self.ignore==False:
                    api.output.warning_msg(self.name,"mapper: Property ",
                        self.part_alias+'.'+self.part_prop," was not defined",
                        stackframe=self.stackframe
                        )
                return ''
            api.output.trace_msg(['parts_mapper','mapper'],spacer,' Property {0} = {1} '.format(self.part_prop,ret))
            penv=pobj.Env
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                
                setattr(pobj,self.part_prop,ret)
                if g_complex_sub[thread_id]==0:
                    api.output.trace_msg(['parts_mapper','mapper'],spacer," Trying to replace value in env[{0}]".format(self.part_prop))
                    api.output.trace_msg(['parts_mapper','mapper'],spacer," Before env value: {0}".format(env[self.part_prop]))
                    api.output.trace_msg(['parts_mapper','mapper'],spacer," Value to set: {0}".format(ret))
                    idx=env[self.part_prop].index("${"+self.name+"('"+self.part_alias+"','"+self.part_prop+"')}")
                    if common.is_list(env[self.part_prop]):
                        if ret != []:
                            env[self.part_prop][idx:idx+1]=ret
                    else:
                        env[self.part_prop]=[ret]
                    api.output.trace_msg(['parts_mapper','mapper'],spacer," After env value: {0}".format(env[self.part_prop]))
                    if ret == []:
                        api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (1) value of {0}".format("''"))
                        return ""
                    else:
                        api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                        return ret[0]
                else:
                    tmp="\1".join(ret)
                    api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(tmp))
                    return tmp
            else:
                tmp= penv.subst(str(ret))
                api.output.trace_msg(['parts_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
                return tmp
            
        except Exception,ec:
            
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
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
            thread_id=thread.get_ident()
            try:
                spacer="."*g_complex_sub[thread_id]
            except KeyError:
                g_complex_sub[thread_id] = 0
                spacer="."*g_complex_sub[thread_id]
            api.output.trace_msg(['partid_mapper','mapper'],spacer,'Expanding value "${{{0}("{1}","{2}","{3}",{4})}}"'.format(self.name,self.part_name,self.ver_range,self.part_prop,self.ignore))
            #Find matching verion pinfo
            pobj=glb.engine._part_manager._from_nvp(
                self.part_name,
                self.ver_range,
                env['TARGET_PLATFORM']
            )
                        
            if pobj is None:
                api.output.trace_msg(['partid_mapper','mapper'],spacer,'Failed to find Part that matches name: {0} version:{1}'.format(self.part_name,self.ver_range))
                if self.ignore:
                    return ''
                self.nvp_to_alias_failed(env)
            api.output.trace_msg(['partid_mapper','mapper'],spacer,' Found matching part! name: {0} version:{1} -> alias: {2}'.format(self.part_name,self.ver_range,pobj.Alias))
            
            ret=getattr(pobj,self.part_prop,None)
            if ret is None:
                if self.ignore==False:
                    api.output.warning_msg(self.name,"mapper: Property ",
                        pobj.Alias+'.'+self.part_prop," was not defined",
                        stackframe=self.stackframe
                        )
                return ''
            api.output.trace_msg(['partid_mapper','mapper'],spacer,' Property {0} = {1} '.format(self.part_prop,ret))
            
            penv=pobj.Env
                
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                #setattr(pobj,self.part_prop,ret)
                if g_complex_sub[thread_id]==0:
                    api.output.trace_msg(['partid_mapper','mapper'],spacer," Trying to replace value in env[{0}]".format(self.part_prop))
                    api.output.trace_msg(['partid_mapper','mapper'],spacer," Before env value: {0}".format(env[self.part_prop]))
                    api.output.trace_msg(['partid_mapper','mapper'],spacer," Value to set: {0}".format(ret))
                    
                    if self.ignore == True:
                        idx=env[self.part_prop].index("${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"',True)}")
                    else:
                        idx=env[self.part_prop].index("${"+self.name+"('"+self.part_name+"','"+str(self.ver_range)+"','"+self.part_prop+"')}")
                    if common.is_list(env[self.part_prop]):
                        if ret != []:
                            env[self.part_prop][0:idx+1]=common.extend_if_absent(env[self.part_prop][0:idx],ret)
                    else:
                        env[self.part_prop]=[ret]
                    api.output.trace_msg(['partid_mapper','mapper'],spacer," After env value: {0}".format(env[self.part_prop]))
                    if ret == []:
                        api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (1) value of {0}".format("''"))
                        return ""
                    else:
                        api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                        return ret[0]
                else:
                    tmp="\1".join(ret)
                    api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(tmp))
                    return tmp
            else:
                tmp= penv.subst(str(ret))
                api.output.trace_msg(['partid_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
                return tmp
            
        except Exception,ec:
            
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
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
    def __init__(self,name,section,part_prop,policy=Policy.REQPolicy.warning):
        mapper.__init__(self)
        self.part_name = name
        #self.ver_range = version.version_range(ver_range)
        self.part_prop = part_prop
        self.policy=policy
        self.section=section

    def __call__(self, target, source, env, for_signature):
        try:
            thread_id=thread.get_ident()
            try:
                spacer="."*g_complex_sub[thread_id]
            except KeyError:
                g_complex_sub[thread_id] = 0
                spacer="."*g_complex_sub[thread_id]
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,'Expanding value "${{{0}("{1}","{2}","{3}",{4})}}"'.format(self.name,self.part_name,self.section,self.part_prop,self.policy))
            pobj_org=glb.engine._part_manager._from_env(env)
            sec=pobj_org.DefiningSection
           #Find matching verion pinfo
            match=part_ref.part_ref(target_type.target_type(self.part_name),pobj_org.Uses)
            if match.hasUniqueMatch:
                pobj=match.UniqueMatch
            else:
                api.output.trace_msg(['partexport_mapper','mapper'],spacer,'Failed to find Part that matches name: {0}'.format(self.part_name))
                self.name_to_alias_failed(env,match,policy=self.policy)
                
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,' Found matching part! name: {0} -> alias: {1}'.format(pobj.Name,pobj.Alias))
            
            ret=pobj.Section(self.section).Exports.get(self.part_prop,[])
            api.output.trace_msg(['partexport_mapper','mapper'],spacer,' Property {0} = {1} '.format(self.part_prop,ret))
            
            psec=pobj.Section(self.section)
            penv=psec.Env
                            
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                #if ret:
                    #pobj.DefiningSection.Exports[self.part_prop]=ret
                if g_complex_sub[thread_id]==0:
                    
                    str_val="${{{0}('{1}','{2}','{3}',{4})}}".format(self.name,self.part_name,self.section,self.part_prop,self.policy)
                    
                    try:
                        # set the value in the exports to prevent recusive hitting of this again latter
                        # value might not exist in cases of programs or components that are on the top 
                        # of the tree.. so if we get a KeyError we can ignore it
                        if common.is_list(sec.Exports[self.part_prop]):
                            api.output.trace_msg(['partexport_mapper','mapper'],spacer," Trying to replace value in export table")
                            api.output.trace_msg(['partexport_mapper','mapper'],spacer," Before Export value: {0}".format(sec.Exports[self.part_prop]))
                            
                            try:
                                idx=sec.Exports[self.part_prop].index(str_val)
                            except ValueError:
                                # index not found.. might be scons 2.1 which would have possibly mapped "foo" to ("foo",) ... only for CPPDEFINES
                                api.output.trace_msg(['partexport_mapper','mapper'],spacer," {0} was not found, trying {0}".format(str_val,(str_val,)))
                                idx=sec.Exports[self.part_prop].index((str_val,))
                                str_val=(str_val,)
                            if ret:
                                sec.Exports[self.part_prop][0:idx+1]=common.extend_if_absent(sec.Exports[self.part_prop][0:idx],ret)
                            else:
                                sec.Exports[self.part_prop].remove(idx)
                            api.output.trace_msg(['partexport_mapper','mapper'],spacer," After export value: {0}".format(sec.Exports[self.part_prop]))
                        else:
                            sec.Exports[self.part_prop]=ret
                    except KeyError:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," Failed to set Export Table value because KeyError")
                    except ValueError:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," Failed to set Export Table value because ValueError")
                        
                    try:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," Trying to replace value in env[{0}]".format(self.part_prop))
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," Before env value: {0}".format(env[self.part_prop]))
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," Value to set: {0}".format(ret))
                        
                        try:
                            idx=env[self.part_prop].index(str_val)
                        except ValueError:
                            # index not found.. might be scons 2.1 which would have possibly mapped "foo" to ("foo",) ... only for CPPDEFINES
                            api.output.trace_msg(['partexport_mapper','mapper'],spacer," {0} was not found, trying {0}".format(str_val,(str_val,)))
                            idx=env[self.part_prop].index((str_val,))
                            str_val=(str_val,)
                            
                        if common.is_list(env[self.part_prop]):
                            if ret != []:
                                env[self.part_prop][0:idx+1]=common.extend_if_absent(env[self.part_prop][0:idx],ret)
                        else:
                            env[self.part_prop]=[ret]
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," After env value: {0}".format(env[self.part_prop]))
                    except KeyError, e:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," KeyError",e)
                    except ValueError, e:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer," ValueError",e)
                    
                    if ret == []:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (1) value of {0}".format("None"))
                        return ''
                    else:
                        api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                        return ret[0]
                else:
                    tmp="\1".join(map(lambda x: "{0}".format(x),ret))
                    api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(tmp))
                    return tmp
            else:
                tmp= penv.subst(str(ret))
                api.output.trace_msg(['partexport_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
                return tmp
            
        except Exception,ec:
            
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
            env.Exit(1)
            
        return ret

class part_lib_mapper(mapper):
    ''' This class maps the part name and version range to the correct alias in 
    the Default enviroment to the actual value stored the in default Env PART_INFO map.
    It then returns the value of the property for the requested part alias. 
    It has to do a small hack to replace a the property in the actual Env else a SCons
    issue with subst and lists causes the subst to fail.
    '''
    name='PARTEXPORTLIB'
    def __init__(self,name,section,part_prop,policy=Policy.REQPolicy.warning):
        mapper.__init__(self)
        self.part_name = name
        self.section= section
        self.part_prop = part_prop
        self.policy=policy

    def __call__(self, target, source, env, for_signature):
        try:
            thread_id=thread.get_ident()
            try:
                spacer="."*g_complex_sub[thread_id]
            except KeyError:
                g_complex_sub[thread_id] = 0
                spacer="."*g_complex_sub[thread_id]
            api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,'Expanding value "${{{0}("{1}","{2}","{3}",{4})}}"'.format(self.name,self.part_name,self.section,self.part_prop,self.policy))
            pobj_org=glb.engine._part_manager._from_env(env)
            sec=pobj_org.DefiningSection
           #Find matching verion pinfo
            match=part_ref.part_ref(target_type.target_type(self.part_name),pobj_org.Uses)
            if match.hasUniqueMatch:
                pobj=match.UniqueMatch
            else:
                api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,'Failed to find Part that matches name: {0}'.format(self.part_name))
                self.name_to_alias_failed(env,match,policy=self.policy)
                
            api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,' Found matching part! name: {0} -> alias: {1}'.format(pobj.Name,pobj.Alias))
            
            ret=pobj.DefiningSection.Exports.get(self.part_prop,[])
            api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,' Property {0} = {1} '.format(self.part_prop,ret))
            
            psec=pobj.Section(self.section)
            penv=psec.Env
                            
            if common.is_list(ret):
                if len(ret)>1:
                    ret=sub_lst(penv,ret,thread_id)
                #if ret:
                    #pobj.DefiningSection.Exports[self.part_prop]=ret
                if g_complex_sub[thread_id]==0:
                    
                    str_val="${{{0}('{1}','{2}','{3}',{4})}}".format(self.name,self.part_name,self.section,self.part_prop,self.policy)
                    
                    try:
                        # set the value in the exports to prevent recusive hitting of this again latter
                        # value might not exist in cases of programs or components that are on the top 
                        # of the tree.. so if we get a KeyError we can ignore it
                        if common.is_list(sec.Exports[self.part_prop]):
                            api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Trying to replace value in export table")
                            api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Before Export value: {0}",sec.Exports[self.part_prop])
                            idx=sec.Exports[self.part_prop].index(str_val)
                            if ret:
                                sec.Exports[self.part_prop][0:idx+1]=common.extend_unique(sec.Exports[self.part_prop][0:idx],ret)
                            else:
                                sec.Exports[self.part_prop].remove(idx)
                            api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," After export value: {0}",sec.Exports[self.part_prop])
                        else:
                            sec.Exports[self.part_prop]=ret
                    except KeyError:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Failed to set Export Table value because KeyError")
                    except ValueError:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Failed to set Export Table value because ValueError")
                        
                    try:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Trying to replace value in env[{0}]".format(self.part_prop))
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Before env value: {0}".format(env[self.part_prop]))
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," Value to set: {0}".format(ret))
                        idx=env[self.part_prop].index(str_val)
                        if common.is_list(env[self.part_prop]):
                            if ret != []:
                                env[self.part_prop][0:idx+1]=common.extend_unique(env[self.part_prop][0:idx],ret)
                        else:
                            env[self.part_prop]=[ret]
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," After env value: {0}".format(env[self.part_prop]))
                    except KeyError, e:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," KeyError",e)
                    except ValueError, e:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer," ValueError",e)
                    
                    if ret == []:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,"Returning (1) value of {0}".format("''"))
                        return ""
                    else:
                        api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,"Returning (2) value of {0}".format(ret[0]))
                        return ret[0]
                else:
                    tmp="\1".join(ret)
                    api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,"Returning (3) value of '{0}'".format(tmp))
                    return tmp
            else:
                tmp= penv.subst(str(ret))
                api.output.trace_msg(['partexportlib_mapper','mapper'],spacer,"Returning (4) value of {0}".format(tmp))
                return tmp            
        except Exception,ec:
            
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
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
    def __init__(self,part_alias,substr,section='build'):
        mapper.__init__(self)
        self.part_alias = part_alias
        self.substr = substr
        self.section=section

    def __call__(self, target, source, env, for_signature):
        try:
            def_env=SCons.Script.DefaultEnvironment()
            
            pobj = glb.engine._part_manager._from_alias(self.part_alias)
            if pobj is None:
                self.alias_missing(env)
                return None
            penv=pobj.Section(self.section).Env
            ret = penv.subst(self.substr)
            
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
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
            pobj=glb.engine._part_manager._from_alias(self.part_alias)
            try:
                ret=pobj.Name
            except AttributeError: 
                self.alias_missing(env)
                return None
            
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
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
            pobj=glb.engine._part_manager._from_alias(self.part_alias)
            
            if pobj is None:
                self.alias_missing(env)
                return None
                
            ret=pobj.ShortName
        except Exception,ec:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.error_msg(
                "Unexpected exception in",self.name,"mapping happened\n"+ec_str.getvalue(),
                stackframe=self.stackframe,
                exit=False
                )
            #because the exception thrown will not get thrown the try catch in subst()
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


import tempfile

class TempFileMunge(mapper):

    """A callable class.  You can set an Environment variable to this,
    then call it with a string argument, then it will perform temporary
    file substitution on it.  This is used to circumvent the long command
    line limitation.

    By default, the name of the temporary file used begins with a
    prefix of '@'.  This may be configred for other tool chains by
    setting '$TEMPFILEPREFIX'.

    env["TEMPFILEPREFIX"] = '-@'        # diab compiler
    env["TEMPFILEPREFIX"] = '-via'      # arm tool chain

    This is the Parts overide of the SCons version of this class
    to address a some complex issues with path handling when on 
    windows and using GNU like tool chains

    todo.. push back into SCons

    """
    name='TEMPFILE'
    def __init__(self, cmd, force_posix_paths = False):
        self.cmd = cmd
        self.force_posix_paths=force_posix_paths

    def __call__(self, target, source, env, for_signature):
        if for_signature:
            # If we're being called for signature calculation, it's
            # because we're being called by the string expansion in
            # Subst.py, which has the logic to strip any $( $) that
            # may be in the command line we squirreled away.  So we
            # just return the raw command line and let the upper
            # string substitution layers do their thing.
            return self.cmd

        # Now we're actually being called because someone is actually
        # going to try to execute the command, so we have to do our
        # own expansion.
        cmd = env.subst_list(self.cmd, SCons.Subst.SUBST_CMD, target, source)[0]
        try:
            maxline = int(env.subst('$MAXLINELENGTH'))
        except ValueError:
            maxline = 2048

        length = 0
        for c in cmd:
            length += len(c)
        if length <= maxline:
            return self.cmd

        # We do a normpath because mktemp() has what appears to be
        # a bug in Windows that will use a forward slash as a path
        # delimiter.  Windows's link mistakes that for a command line
        # switch and barfs.
        #
        # We use the .lnk suffix for the benefit of the Phar Lap
        # linkloc linker, which likes to append an .lnk suffix if
        # none is given.
        (fd, tmp) = tempfile.mkstemp('.lnk', text=True)
        native_tmp = SCons.Util.get_native_path(os.path.normpath(tmp))

        if env['SHELL'] and env['SHELL'] == 'sh':
            # The sh shell will try to escape the backslashes in the
            # path, so unescape them.
            native_tmp = native_tmp.replace('\\', '/')
            # In Cygwin, we want to use rm to delete the temporary
            # file, because del does not exist in the sh shell.
            rm = env.Detect('rm') or 'del'
        else:
            # Don't use 'rm' if the shell is not sh, because rm won't
            # work with the Windows shells (cmd.exe or command.com) or
            # Windows path names.
            rm = 'del'

        prefix = env.subst('$TEMPFILEPREFIX')
        if not prefix:
            prefix = '@'

        args = list(map(SCons.Subst.quote_spaces, cmd[1:]))
        data=" ".join(args)
        #This is a little bit of a hack as it could mess up switches using '\'
        # however this is unlikely as windows uses / or - for switchs and posix uses - or --
        if self.force_posix_paths:
            data= data.replace('\\', '/')
        os.write(fd, data + "\n")
        os.close(fd)
        # XXX Using the SCons.Action.print_actions value directly
        # like this is bogus, but expedient.  This class should
        # really be rewritten as an Action that defines the
        # __call__() and strfunction() methods and lets the
        # normal action-execution logic handle whether or not to
        # print/execute the action.  The problem, though, is all
        # of that is decided before we execute this method as
        # part of expanding the $TEMPFILE construction variable.
        # Consequently, refactoring this will have to wait until
        # we get more flexible with allowing Actions to exist
        # independently and get strung together arbitrarily like
        # Ant tasks.  In the meantime, it's going to be more
        # user-friendly to not let obsession with architectural
        # purity get in the way of just being helpful, so we'll
        # reach into SCons.Action directly.
        if SCons.Action.print_actions:
            print("Using tempfile "+native_tmp+" for command line:\n"+
                  str(cmd[0]) + " " + " ".join(args))
        return [ cmd[0], prefix + native_tmp + '\n' + rm, native_tmp ]



api.register.add_mapper(part_mapper)
api.register.add_mapper(part_id_mapper)
api.register.add_mapper(part_id_export_mapper)
api.register.add_mapper(part_subst_mapper)
api.register.add_mapper(part_name_mapper)
api.register.add_mapper(part_shortname_mapper)
api.register.add_mapper(abspath_mapper)
api.register.add_mapper(relpath_mapper)
api.register.add_mapper(part_lib_mapper)
api.register.add_mapper(TempFileMunge)

api.register.add_bool_variable('MAPPER_BAD_ALIAS_AS_WARNING',True,'Controls if a missing alias is an error or a warning')
