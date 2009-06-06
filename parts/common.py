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

g_builders={}
#g_args={}
g_env_cache={}
g_parts_objs={}

g_part_mode=''

# node we have processed
#g_parts_node=set()
# enviroments with builders
# or ones that are used created by the part call which we always assume to have one
#g_env_w_builders=set()

#def_args={}
def_vars=[]
g_defaultoverides={}
# holds the set of alias that are created by parts
g_name_alias_map={}
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


g_base_env= SCons.Script.Environment(tools=[])
def get_basic_SCon_env(**kw):
    return g_base_env.Clone(**kw)

def add_mapper(mapper):
    g_mappers[mapper.name]=mapper

def add_parts_object(key,object):
    g_parts_objs[key]=object
    # add code to for help generation

def AddVariable(key,default,help,validator=None,converter=None):
    '''Generic varible addition'''
    #def_args[key]=default
    def_vars.append((key,help,default,validator,converter))

def AddBoolVariable(key,default,help):
    '''Generic varible addition'''
    def_vars.append(SCons.Script.BoolVariable(key,help,default))    

def AddEnumVariable(key,default,help,allowed_values,map={},ignorecase=1):
    '''Generic varible addition'''
    def_vars.append(SCons.Script.EnumVariable(key,help,default))

def AddListVariable(key,default,help,allowed_values=[],map={}):
    '''Generic varible addition'''
    def_vars.append(Variables.ListVariable2(key,help,default,allowed_values,map))    

##########################################################


###############
import env_overrides
class namespace(dict,env_overrides.bindable):
    ''' helper class to allow making subst varaible in SCons to allow a clean
    form of $a.b
    '''
    def __init__(self,**kw):
        dict.__init__(self,kw)

    def __getattr__(self,name):
        ''' This is ugly but because SCons does not have a good recursive subst
        code, I need to subst stuff here before SCons can try to, else it will
        try to set this object to Null string, causing an unwanted error'''
        #print "Get **************", name, self[name]
        return self.env.subst(self[name])
    def __setattr__(self,name,value):
        self[name]=value
    def __delattr__(self,name):
        del self[name]
        
    def _rebind(self,env,key):
        '''
        Rebind the environment to a new one.
        There does not seem a way to have this happen in a clone
        as from what i can see semi_deep_copy does not pass a new env
        However I can do this in cases when i do a copy, which is not as
        bad as not doing it at all
        '''
        tmp=namespace(**self.copy())
        tmp._bind(env,key)
        return tmp
    def _bind(self,env,key):
        self.__dict__['env']=env



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
            if type(i) == type([]):
                tmp.extend(i)
            else:
                tmp.append(i)
    return tmp    

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
        # we coudl error .. but instead I return the to_path
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
    s='env.'+func+'('
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
    
    alias=env.subst('$ALIAS')
    if g_name_alias_map.has_key(alias)==False:
        g_name_alias_map[alias]=set()
    
    
    name=env.subst(concept+'${PART_NAME}_${PART_VERSION}')
    g_name_alias_map[alias].add(name)
    
    if action ==None:
        n_ver_alias=env.Alias(name, name_version)
    else:
        n_ver_alias=env.Alias(name, name_version, action)
    
    name=env.subst(concept+'${PART_NAME}_${PART_SHORT_VERSION}')
    g_name_alias_map[alias].add(name)
    if name_shortversion == None:
        n_sver_alias=env.Alias(name, n_ver_alias)
    else:
        n_sver_alias=env.Alias(name, [n_ver_alias,name_shortversion])
        
    
    name=env.subst(concept+'${PART_NAME}_')+str(env.PartVersion().major())
    g_name_alias_map[alias].add(name)
    if name_majorversion == None:
        n_mver_alias=env.Alias(name, n_sver_alias)
    else:
        n_mver_alias=env.Alias(name, [n_sver_alias,name_majorversion])
    
    name=env.subst(concept+'${PART_NAME}')
    g_name_alias_map[alias].add(name)
    if name_only == None:
        name_alias=env.Alias(name, n_mver_alias)
    else:
        name_alias=env.Alias(name, [n_mver_alias,name_only])
        
    if always_build:
        env.AlwaysBuild(n_ver_alias)
        env.AlwaysBuild(n_sver_alias)
        env.AlwaysBuild(n_mver_alias)
        env.AlwaysBuild(name_alias)
    
    # clean up thsi statement once we clean up the Part vars
    if env['PART_INFO']['PARENT_ALIAS'] != None:
        def_env=SCons.Script.DefaultEnvironment()
        parent_env=def_env['PART_INFO'][env['PART_INFO']['PARENT_ALIAS']]['ENV']
        return make_alias_tree(parent_env,concept,n_ver_alias,n_sver_alias,n_mver_alias,name_alias,always_build=always_build)
    
    return name_alias


def load_module(root,name):
    """Return the imported module for some platform.
    
    Taken from SCons platform.. and made more generic so Parts can reuse the logic
    instead of using the C&P anit-patttern.

    """
    full_name = root+'.' + name
    #print full_name,sys.modules.has_key(full_name)
    if not sys.modules.has_key(full_name):
        try:
            file, path, desc = imp.find_module(name,
                                sys.modules[root].__path__)
            try:
                mod = imp.load_module(full_name, file, path, desc)
            finally:
                if file:
                    file.close()
        except ImportError:
            try:
                import zipimport            
                importer = zipimport.zipimporter( sys.modules[root].__path__[0] )
                mod = importer.load_module(full_name)                    
            except ImportError:
                raise SCons.Errors.UserError, "No %s named '%s'" % (root,name)
        #setattr(???, name, mod) # was in orginal SCons code.. however i don't get it

    return sys.modules[full_name]

AddVariable('ALIAS_SEPARTATOR','::','seperator used to seperate namespace concepts from general alias value')