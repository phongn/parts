
import common
import reporter

_added_types={}

class Policy(object):
    ignore=0
    warning=1
    error=2

class requirement(object):
    def __init__(self, key, internal=False, public=None, policy=None, mapper=None,listtype=None):
        ''' Sets up the requirment object
        
        @param value The value to import
        @param internal True is the value should not be added to current Parts export table, False otherwise
        @param public True to value to global 'env' space, instead of just the namespace in the env object
        @param policy how to handle an item that could not be mapped, can be ignore, warn, or error
        @param mapper The mapper object to use for delayed mapping in classic formats, defaults to PARTIDEXPORTS
        @param listtype Tells if this type is a list type or not.. 
        '''
        self._key=key
        self._internal=internal
        
        if public is None:
            self._public=False
        else:
            self._public=public
            
        if policy is None:
            self._policy=Policy.warning
        else:
            self._policy=policy
        
        if listtype is None:
            # do some simple check for seeing if this value should be treated as a list
            # ie XXXFLAGS,XXXDEFINES,XXXPATH ( add more as needed )
            if self.key.endswith('FLAGS') or\
                self.key.endswith('DEFINES') or\
                self.key.endswith('PATH'):
                  self._listtype=True
                  if public is None:
                      self._public=False
                  if policy is None:
                      self._policy=Policy.ignore
            else:
                  self._listtype=False
        else:
            self._listtype=listtype
        
        if mapper is not None:
            self._mapper=mapper
        else:
            self._mapper='PARTIDEXPORTS'
    
    def value_mapper(self,value):
        return "${{{0}{1}}}".format(self._mapper,value)
    
    @property
    def is_list(self):
        return self._listtype
    
    @property
    def is_public(self):
        return self._public
    
    @property
    def is_internal(self):
        return self._internal    
    
    @property
    def key(self):
        return self._key    
    
    def __call__(self,internal=None, public=None, policy=None):
        if internal is not None:
            self._internal=internal
        if public is not None:
            self._public=public
        if policy is not None:
            self._policy=policy
        return self
    
    def __or__(self,lhs):
        if common.is_int(lhs):
            return REQ([self])
        return REQ([self])|lhs
    
    def __ror__(self,rhs):
        if common.is_int(rhs):
            return REQ([self])
        return REQ([self])|rhs
    
    def __ior__(self,lhs):
        if common.is_int(lhs):
            return REQ([self])
        return REQ([self])|lhs
    
    def __str__(self):
        return "requirement(key={0} internal={1} public={2} policy={3})".format(self.key,self._internal,self._public,self._policy)
    def __repr__(self):
        return "requirement(key={0} internal={1} public={2} policy={3})".format(self.key,self._internal,self._public,self._policy)
    def __hash__(self):
        return hash(self.key)
    
    def __cmp__(self,rhs):
        return cmp(self.key,rhs.key)

class requirement_set(object):
    def __init__(self,lst):    
        self._values=[]
        for i in lst:
            if type(i) is type(''):
                if i in _added_types:
                    tmp=_added_types[i][0]
                    self._values.extend(tmp._values)
                    if _added_types[i][1] != Policy.ignore:
                        reporter.report_warning("REQ option {0} is deprecated and will be removed, please remove usage.".format(i))
                else:
                    reporter.report_warning("{0} is not a registered REQ type. Skipping...".format(i))
            else:
                self._values.append(i)

    
    def __call__(self,internal=None,public=None, policy=None):
        if internal is not None:
            self._internal=internal
        if public is not None:
            self._public=public
        if policy is not None:
            self._policy=policy            
        return self
    
    def __or__(self,lhs):
        if common.is_int(lhs):
            return REQ(self._values)
        return REQ(self._values)|lhs
    
    def __ror__(self,rhs):
        if common.is_int(rhs):
            return REQ(self._values)
        return REQ(self._values)|rhs
    
    def __ior__(self,lhs):
        if common.is_int(lhs):
            return REQ(self._values)
        return REQ(self._values)|lhs
            

def DefineRequirementSet(name,lst,policy=Policy.ignore):
        tmplst=[]
        global _added_types
        for i in lst:
            if isinstance(i,requirement):
                tmplst.append(i)
            elif type(i) is type(''):
                try:
                    tmplst.extend(_added_types[i][0]._values)
                    if _added_types[i][1] != Policy.ignore:
                        reporter.report_warning("REQ option {0} is deprecated and will be removed, please remove usage.".format(i))
                except KeyError:
                    reporter.report_warning(i ,"not found when mapping requirments")
        _added_types[name]=(requirement_set(tmplst),policy)
                    
        
class requirement_internal(requirement):
    def __call__(self,public=None, policy=None):
        if public:
            self._public=public
        if policy:
            self._policy=policy
        return self 

class requirement_set_internal(requirement_set):
    def __call__(self,public=None, policy=None):
        
        for i in self.__values:
            i(internal,public,policy)
            
        return self



# setup default value for common stuff... some of this should move to tools that define them
DefineRequirementSet('EXISTS',[])
DefineRequirementSet('CPPPATH',[requirement('CPPPATH',public=True,policy=Policy.ignore)])
DefineRequirementSet('CPPDEFINES',[requirement('CPPDEFINES',public=True,policy=Policy.ignore)])
DefineRequirementSet('CXXFLAGS',[requirement('CXXFLAGS',public=True,policy=Policy.ignore)])
DefineRequirementSet('CFLAGS',[requirement('CFLAGS',public=True,policy=Policy.ignore)])
DefineRequirementSet('CCFLAGS',[requirement('CCFLAGS',public=True,policy=Policy.ignore)])
DefineRequirementSet('LINKFLAGS',[requirement('CCFLAGS',public=True,policy=Policy.ignore)])
DefineRequirementSet('LIBPATH',[requirement('LIBPATH',public=True,policy=Policy.ignore)])

DefineRequirementSet('HEADERS',['CPPPATH','CPPDEFINES'])
DefineRequirementSet('LIBS',['LIBPATH',requirement('LIBS',public=True,policy=Policy.ignore,mapper='PARTLIB',listtype=True)])
DefineRequirementSet('default',['LIBS','HEADERS'])
DefineRequirementSet('DEFAULT',['default'])

DefineRequirementSet('ALL_DEFAULT',['LIBS','HEADERS','CCFLAGS','CFLAGS','CXXFLAGS'],Policy.warning)


class metaREQ(type):
    
    def __getattr__(self,name):
        internal=False
        if name.lower().endswith('_internal'):
            name=name[:-len('_internal')]
            internal=True
        
        if name in _added_types:
            if _added_types[name][1] != Policy.ignore:
                reporter.report_warning("REQ option {0} is deprecated and will be removed, please remove usage.".format(name))
            return _added_types[name][0](internal=internal)
        if internal:
            return requirement_internal(name,internal)
        return requirement(name,internal)
    
    
class REQ(set):
    __metaclass__ = metaREQ
    
