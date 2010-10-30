###########
## Common code and general objects
##########

import fnmatch
import string
import os
import imp
import sys

import Variables

# import Scons stuff
import SCons.Script 
import SCons.Errors
import SCons.Tool
import SCons.Util


g_build_context_files=set()

g_engine=None
g_part_frame=[]

g_builders={}
#g_args={}
g_env_cache={}
# global object to add to parts call
g_parts_objs={}


#g_parts={} 
#g_name_alias={}
# state object of what is being processed.
g_part_being_processed=[]

def_vars=[]
## adding stuff here as the Varible are falling apart on handing objects
g_defaultoverides={'PACKAGE_GROUP_FILTER':{}}

# set of the part we know we want to build
g_buildable_part=set()
# set of alias we are targeting to be build as source
g_target_alias=set()
#set of parts we want to build as an SDK, given that it exists in the sdk directory
g_build_as_sdk=set()
#depends data we stored
g_depends_data={}
# custom data mappers
g_mappers={}
# these are the global functions we define to the SConstruct
g_globals={}
# these are all teh sections that have been defined
g_sections=set()

# path to where Parts is installed
g_parts_path=os.path.abspath(os.path.split(__file__)[0])

# for packaging support 
_INSTALLED_PACKAGING_GROUPS={}
_INSTALLED_NO_PACKAGING_GROUPS={}


g_base_env= SCons.Script.Environment(tools=[])
def get_basic_SCon_env(**kw):
    return g_base_env.Clone(**kw)

def add_section(section):
    # add
    g_sections.add(section)
    
def add_mapper(mapper):
    g_mappers[mapper.name]=mapper

def add_parts_object(key,object):
    g_parts_objs[key]=object
    # add code to for help generation
    
def add_global_value(key,object):
    g_globals[key]=object

def AddVariable(key,default,help,validator=None,converter=None):
    '''Generic varible addition'''
    #def_args[key]=default
    def_vars.append((key,help,default,validator,converter))

def AddBoolVariable(key,default,help):
    '''Generic varible addition'''
    def_vars.append(SCons.Script.BoolVariable(key,help,default))    

def AddEnumVariable(key,default,help,allowed_values,map={},ignorecase=1):
    '''Generic varible addition'''
    def_vars.append(SCons.Script.EnumVariable(key,help,default,allowed_values,map,ignorecase))

def AddListVariable(key,default,help,allowed_values=[],map={}):
    '''Generic varible addition'''
    def_vars.append(Variables.ListVariable2(key,help,default,allowed_values,map))    

##########################################################


def is_processing_part(part_obj):
    # we this part is processed that we don't need to worry about it
    if part_obj.IsProcessed():
        return False
    # check to see if the "root" part is being processed
    # as if this is the case we don't want to process it again
    if part_obj.root.alias in g_part_being_processed:
        return True
    return False
    
def try_load_part_component(env,comp):
    curr_define_part=get_part(env)
    name_list=comp.name.split('.')[0]
    root_name=name_list[0]
    ver_range=comp.version
    
    # try to see if we can resolve the component 
    
    # Check DB for match
    
    # If that failed try manual laoding of Parts till we get a hit
    # or detact deadlock
    
    # first we try to find something that looks likes it
    
    # check to see if we are laoding a sub part
    
    # here we try to find the best match root part
    
        
    
    # then we just start load stuff till we get a hit
    
    # if that fails return None to have calling code
    # add a mapper to resolve latter or error out


###############
# this class allows us to add object varible that get a reference to the env
# that holds it
class bindable(object):
    pass 

class DelayVariable(object):
    ''' This class defines a varable that will not be evaluted until it is requested
    This allow it to be assigned some logic and not execute it till requested, as needed
    The class will reset the value in the SCons Environment with the delayed value
    once it is evaluated
    '''    
    def __init__(self,func):
        self.__func=func
    def __eval__(self):
        return self.__func()
    def __str__(self):
        return str(self.__eval__())
    
    
class namespace(dict,bindable):
    ''' helper class to allow making subst varaible in SCons to allow a clean
    form of $a.b
    '''
    def __init__(self,**kw):
        dict.__init__(self,kw)

    def __getattr__(self,name):
        ''' This is ugly but because SCons does not have a good recursive subst
        code, I need to subst stuff here before SCons can try to, else it will
        try to set this object to Null string, causing an unwanted error'''
        tmp=self[name]
        if hasattr(tmp,'__eval__'):
            tmp=tmp.__eval__()
            self[name]=tmp
        if (is_string(tmp) or tmp is None) and self.__dict__.has_key('env'):
            return self.env.subst(tmp)
        return tmp
    
    def __setattr__(self,name,value):
        self[name]=value
    def __delattr__(self,name):
        del self[name]
        
    def _rebind(self,env,key):
        '''
        Rebind the environment to a new one.
        There does not seem a way to have this happen in a clone
        as from what I can see semi_deep_copy does not pass a new env
        Howevere I have updated the overrides to handle the clone of objects
        that are bindable to the env to be cloned and handled better.
        '''
        tmp=namespace(**self.copy())
        tmp._bind(env,key)
        return tmp
    
    def _bind(self,env,key):
        self.__dict__['env']=env
        
    def clone(self):
        tmp=namespace(**self.copy())
        tmp._bind(None,None)
        return tmp


def process_tool_arg(lst):
    tmplst=[]
    for i in lst:
        if is_string(i):
            tmp=string.split(i,'_',2)
        else:
            tmp=i
        if len(tmp)==1:
            tmp.append(None)
        elif len(tmp)!=2:
            # error
            print "Invalid tool defined [",tmp,']'
            Exit(1)
        elif tmp[1]=='':
            tmp[1]=None
        tmplst.append(tmp)
    tmplst.reverse()
    return tmplst

def AddBuilder(name,builder):
    if g_builders.has_key(name)==False:
        g_builders[name]=builder
    else:
        pass
        

def matches(value, includes, excludes=None):
    '''Function help with tell if a value (as a string) matched on of the include
    patterns and doesn't match on of the exclude patterns.
    '''
    match = 0
    for pattern in includes:
        if fnmatch.fnmatchcase(value, pattern):
            match = 1
            break
    if match == 1:
       for pattern in excludes:
           if fnmatch.fnmatchcase(value, pattern):
               match = 0
               break
    return match

def make_list(obj):
    ''' 
    The purpose of thsi function is to make the obj into a list if it is not
    already one. It will flatten as well    
    '''
    if SCons.Util.is_List(obj):
        return SCons.Util.flatten(obj)
    return [obj]

def make_unique(obj):
    ''' The purpose of this object is to make a list
    with only unique values in it.
    The input is the list object.
    It returns the new list (Note this is NOT a deep copy)'''
    tmp=[]
    for i in obj:
        if not i in tmp:
            #if type(i) == type([]):
            #    tmp.extend(i)
            #else:
            tmp.append(i)
    return tmp

def extend_unique(obj,lst):
    ''' 
    The purpose of this funtion is to add the items in the collection
    to a list in a unique way
    '''
    for i in lst:
        append_unique(obj,i)
    return obj

def pre_extend_unique(obj,lst):
    ''' 
    The purpose of this funtion is to add the items in the collection
    to a list in a unique way
    '''
    
    for i in lst:
        prepend_unique(obj,i)
    return obj

def append_unique(obj,val):
    ''' The purpose of this funtion is to add the object to a list in a unique way'''
    if not val in obj:
        obj.append(val)
    else:
        obj.remove(val)
        obj.append(val)
    return obj

def prepend_unique(obj,val):
    ''' The purpose of this funtion is to add the object to a list in a unique way'''
    if not val in obj:
        obj[0:0]=[val]
    else:
        obj.remove(val)
        obj[0:0]=[val]
    
    return obj

def append_if_absent(obj,val):
    if not val in obj:
        obj.append(val)
    return obj

def extend_if_absent(obj,val):
    ''' The purpose of this funtion is to add to the object only the list elements which are unique'''
    
    for element in val:
        if element not in obj:
            obj.append(element)
    return obj


def make_unique_str(obj):
    ''' The purpose of this object is to make a list
    with only unique values in it.
    The input is the list object.
    It returns the new list (Note this is NOT a deep copy)'''
    tmp=[]
    for i in obj:
        addit=True
        for j in tmp:
            if str(j) == str(i):
                 addit=False
                 break 
        if addit:
            tmp.append(i)
    return tmp

def is_list(obj):
    return SCons.Util.is_List(obj)

def is_dictionary(obj):
    return SCons.Util.is_Dict(obj)

def is_string(obj):
    return SCons.Util.is_String(obj)

def is_bool(obj):
    return obj is bool()

def is_int(obj):
    return type(obj) is int()

def is_float(obj):
    return type(obj) is float()

def is_catagory_file(env,cat,file):
    ''' this function is the master function for finding a if a file matches a type pattern.'''
    '''This function returns True if the argument looks like a file that would be copied to a LIB directory'''
    patterns=env[cat]
    for i in patterns:
        if fnmatch.fnmatchcase(str(file),i):
            return True;
    return False

def option_bool(val,option, default=False):
    if is_string(val):
        if val.lower() == 'true':
            return True
        elif val.lower() == 'false':
            return False
        else:
            print 'Parts:',option,'set to invalid value of [',val,'], using default of value of [',default,']'
            return default
    return bool(val)    

#def is_lib_file(env,file):
#    '''This function returns True if the argument looks like a file that would be copied to a LIB directory'''
#    return is_catagory_file(env,'LIB_PATTERN',file)

#def is_bin_file(env,file):
#    '''This function returns True is the argument looks like a file that would be copied to a BIN directory'''
#    return is_catagory_file(env,'BIN_PATTERN',file)

def tag_node_ownership(env,node):
    alias=env['PART_ALIAS']
    tmp=env.MetaTagValue(node,'owners','parts',[])
    if alias not in tmp:
        #print "Tagged",alias, node
        env.MetaTag(node,'parts',owners=[alias]+tmp)
        
    tmp=env.MetaTagValue(node.srcnode(),'owners','parts',[])
    if alias not in tmp:
        #print "Tagged",alias, node.srcnode()
        env.MetaTag(node.srcnode(),'parts',owners=[alias]+tmp)
    
    for k,e in node.entries.items():
        if isinstance(e,SCons.Node.FS.Dir) and k != '.' and k!='..':
            tag_node_ownership(env,e)


## amazing enough python never added a relpath function....
def relpath(to_dir, from_dir=os.curdir):
    """
    Return a relative path to the target [to_dir] from either the current dir or an optional base dir(from_dir).
    Base can be a directory specified either as absolute or relative to current dir.
    Does not check to see if directories exist.. assumes you get that right yourself
    Also in drive based systems.. it returns the abs_path(to_dir) in cases of different drives
    """
    
    from_dir_list = (os.path.abspath(from_dir)).split(os.sep)
    to_dir_list = (os.path.abspath(to_dir)).split(os.sep)
    
    # On the windows platform the target may be on a completely different drive from the base.
    if os.name in ['nt','dos','os2'] and from_dir_list[0] != to_dir_list[0]:
        # we could error .. but instead I return the to_path
        return os.path.abspath(to_dir)

    # Starting from the filepath root, work out how much of the filepath is
    # shared by base and target.
    for i in range(min(len(from_dir_list), len(to_dir_list))):
        if from_dir_list[i] != to_dir_list[i]: break
    else:
        # If we broke out of the loop, i is pointing to the first differing path elements.
        # If we didn't break out of the loop, i is pointing to identical path elements.
        # Increment i so that in all cases it points to the first differing path elements.
        i+=1

    rel_list = [os.pardir] * (len(from_dir_list)-i) + to_dir_list[i:]
    if rel_list == []:
        return '.'
    return os.path.join(*rel_list)



#---------------------------------------------------------------------
# parseVersionNumber
#
# Parses a version number string such as '8.1.0' and returns 
# major_number, minor_number, and revision_number.  For any of these
# fields, a value of -1 means 'any'.  For example, '8.x.1' would return
# 8, -1, and 1.  The given version number string must not start with a 
# product prefix.
#
# Returns (error_msg, major_number, minor_number, revision_number).
# error_msg is an empty string if there is no error.
#---------------------------------------------------------------------
def parseVersionNumber(versionNumber):
    fields = string.split(versionNumber, '.')
    fieldValues = [-1, -1, -1]		# default values

    for i in range(len(fields)):
        if fields[i] == 'x' or fields[i] == 'X' or fields[i] == '*':
            value = -1
        else:
            value = int(fields[i])

        fieldValues[i] = value
        # Parse only as many version numbers as we have room for
        if i + 1 == len(fieldValues):
            break

    return fieldValues[0], fieldValues[1], fieldValues[2]

#---------------------------------------------------------------------
# CompareVersionNumbers
#
# Compares two discrete version numbers and returns (error_msg, result) 
# where error_msg is an emptry string if there is no error.  
# result contains the result of the comparison
# as follows:
#
#	result = 0:	versionNumber1 = versionNumber2
#	result < 0:	versionNumber1 < versionNumber2
#	result > 0: versionNumber1 > versionNumber2
#
# Arguments must be in the discrete version string format, e.g. '8.1.2'.
# Argument of None is considered to be less than '0.0.0'
#
# Returns (error_message, result) where error_message is '' if no error.
#---------------------------------------------------------------------
def CompareVersionNumbers(verStr1, verStr2):
    if verStr1 == None and verStr2 == None:
        return 0

    if verStr1 == None and verStr2 != None:
        return -1

    if verStr1 != None and verStr2 == None:
        return 1

    major1, minor1, rev1 = parseVersionNumber(verStr1)

    major2, minor2, rev2 = parseVersionNumber(verStr2)

    if major1 < major2 and not (major1 == -1 or major2 == -1):
        return -1
    if major1 > major2 and not (major1 == -1 or major2 == -1):
        return 1

    if minor1 < minor2 and not (minor1 == -1 or minor2 == -1):
        return -1
    if minor1 > minor2 and not (minor1 == -1 or minor2 == -1):
        return 1

    if rev1 < rev2 and not (rev1 == -1 or rev2 == -1):
        return -1
    if rev1 > rev2 and not (rev1 == -1 or rev2 == -1):
        return 1

    return 0

def get_version_from_list(v, vlist):
    for vi in vlist:
        if CompareVersionNumbers(vi,v) == 0:
            return vi
    return False

    
## help objects
class _make_rel:
    def __init__(self,lst):
        self.lst=lst
    
    def string_it(self,env,path):
        import pattern
        ret='[ '
        for i in self.lst:
            if isinstance(i,SCons.Node.FS.Dir):
                ret+="env.Dir('"+relpath(env.Dir(i).srcnode().abspath,path)+"')"
            elif isinstance(i,pattern.Pattern):
                t,sr=i.target_source(path)
                inc=[]
                for s in sr:
                    inc.append(relpath(s,path).replace('\\','/'))
                #installed_files+=env.InstallAs(t,sr)
                s = 'Pattern(src_dir="'+relpath(i.src_dir.abspath,path).replace('\\','/')+'",includes = '+str(inc)
                if i.sub_dir!='':
                    s += ",sub_dir='"+str(i.sub_dir)+"'"
                s+=")"
                ret+=s
            else:
                ret+="'"+relpath(env.File(i).srcnode().abspath,path).replace('\\','/')+"'"
            ret+=','
        ret=ret[:-1]+']'
        return ret



class _make_reld:
    def __init__(self,lst):
        self.lst=lst
    
    def string_it(self,env,path):
        ret=[]
        for i in self.lst:
            if isinstance(i,SCons.Node.FS.Dir):
                ret.append("env.Dir("+relpath(env.Dir(i).srcnode().abspath,path)+")")
            else:
                ret.append(relpath(env.Dir(i).srcnode().abspath,path))
        return str(ret)

class named_parms:
    def __init__(self,_kw):
        self.kw=_kw
    
    def string_it(self,env,path):
        ret=""
        i=len(self.kw)
        for k,v in self.kw.items():
            i=i-1
            ret+=str(k)+"="+gen_arg(env,path,v)
            if i>0:
                ret+=','
        if ret=='':
            ret='**{}'
        return ret  


def gen_arg(env,sdk_path,value):
    ret=''
    if isinstance(value,_make_rel):
        ret+=value.string_it(env,sdk_path)
    elif isinstance(value,_make_reld):
        ret+=value.string_it(env,sdk_path)
    elif isinstance(value,named_parms):
        ret+=value.string_it(env,sdk_path)
    elif is_string(value):
        ret+="'"+env.subst(value)+"'"
    else:
        ret+=str(value)
    return ret

def func_gen(env,sdk_path,func,values):
    s='    env.'+func+'('
    i=len(values)
    for v in values:
        i=i-1
        s+=gen_arg(env,sdk_path,v)
        if i>0:
            s+=','
    s+=')'
    return s


def make_alias_tree(env,concept,
    name_version,
    name_shortversion=None,
    name_majorversion=None,
    name_only=None,
    action=None,
    always_build=False):
    
    pobj=g_engine._part_manager._from_env(env)
        
    name="%s%s_%s"%(concept,pobj.Name,pobj.Version)#env.subst(concept+'${PART_NAME}_${PART_VERSION}')
    pobj._add_alias(name)
    #print name,"->",name_version[0]
    if action ==None:
        n_ver_alias=env.Alias(name, name_version)
    else:
        n_ver_alias=env.Alias(name, name_version, action)
    
    name="%s%s_%s"%(concept,pobj.Name,pobj.ShortVersion)#env.subst(concept+'${PART_NAME}_${PART_SHORT_VERSION}')
    pobj._add_alias(name)
    #print name,"->",n_ver_alias[0]
    if name_shortversion == None:
        n_sver_alias=env.Alias(name, n_ver_alias)
    else:
        n_sver_alias=env.Alias(name, [n_ver_alias,name_shortversion])
        
    
    name="%s%s_%s"%(concept,pobj.Name,pobj.Version.major())#env.subst(concept+'${PART_NAME}_')+str(env.PartVersion().major())
    pobj._add_alias(name)
    #print name,"->",n_sver_alias[0]
    if name_majorversion == None:
        n_mver_alias=env.Alias(name, n_sver_alias)
    else:
        n_mver_alias=env.Alias(name, [n_sver_alias,name_majorversion])
    
    name="%s%s"%(concept,pobj.Name)#env.subst(concept+'${PART_NAME}')
    pobj._add_alias(name)
    #print name,"->",n_mver_alias[0]
    if name_only == None:
        name_alias=env.Alias(name, n_mver_alias)
    else:
        name_alias=env.Alias(name, [n_mver_alias,name_only])
        
    if always_build:
        env.AlwaysBuild(n_ver_alias)
        env.AlwaysBuild(n_sver_alias)
        env.AlwaysBuild(n_mver_alias)
        env.AlwaysBuild(name_alias)
    
    # clean up this statement once we clean up the Part vars

    if pobj.Parent is not None:
        parent_env=pobj.Parent.Env
        return make_alias_tree(parent_env,concept,n_ver_alias,n_sver_alias,n_mver_alias,name_alias,always_build=always_build)
    
    return name_alias


############################## Platform Maps ################################
import re
g_arch_map = {
'ia32':'x86',
'x86':'x86',
'i386':'x86',
'i486':'x86',
'i586':'x86',
'i686':'x86',
'x64':'x86_64',
'AMD64':'x86_64',
'amd64':'x86_64',
'em64t':'x86_64',
'EM64T':'x86_64',
'x86_64':'x86_64',
'IA64':'ia64',
'ia64':'ia64',
'any':'any'
}

g_os_map = {
'win32':'win32',
'win64':'win32',
'xp':'win32',
'vista':'win32',
'win7':'win32',
'windows':'win32',
'posix':'posix',
'linux':'posix',
'fedora':'posix',
'rhel':'posix',
'ubuntu':'posix',
'hp-ux':'hp-ux',
'os2':'os2',
'cygwin':'cygwin',
'suse':'posix',
'sles':'posix',
'sunos':'sunos',
'solaris':'sunos',
'darwin':'darwin',
'mac':'darwin',
'macos':'darwin',
'any':'any'
}

g_valid_arch = []
g_valid_os =[]
g_valid_platform_re = re.compile("a")

def UpdatePlatformRegEx():
    global g_valid_platform_re
    arch_str = ''
    os_str = ''
    for arch in g_valid_arch:
        if arch_str == '':
            arch_str = arch_str + arch
        else:
            arch_str = arch_str + '|' + arch
            
    for os in g_valid_os:
        if os_str == '':
            os_str = os_str + os
        else:
            os_str = os_str + '|' + os
   
    g_valid_platform_re = re.compile('(?P<os>' + os_str + ')?(?P<sep1>-)?(?P<arch>' + arch_str + ')?$',re.IGNORECASE)

    
def UpdateValidArchList():
    for k,v in g_arch_map.items():
        if k not in g_valid_arch:
            g_valid_arch.append(k)
    g_valid_arch.sort(lambda a,b: cmp(len(b),len(a)))
    UpdatePlatformRegEx()

def UpdateValidOSList():
    for k,v in g_os_map.items():
        if k not in g_valid_os:
            g_valid_os.append(k)
    g_valid_os.sort(lambda a,b: cmp(len(b),len(a)))
    UpdatePlatformRegEx()

UpdateValidArchList()
UpdateValidOSList()






