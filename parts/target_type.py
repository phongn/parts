import common
import reporter

def _parse_target(target):
    '''
    Parses the Target to help Parts figure out how to treat the Target
    
    The current logic is to handle cases such as:
        alias::<part_alias>
        <part name>
        name::<part name>
        name::<part name>@key:value
        name::<part name>@key:value@key2:val2 ...
        <concept>::<some form from above>
        
    '''
    if target is None:
        return {}
    elif target == 'all':
        return {'all':True}
    seperator=common.g_engine.def_env.subst("$ALIAS_SEPARTATOR")
    t=target.split(seperator,1)   
    # this is a the case of "foo"
    if len(t) == 1:
        # we have an part name, SCons alias or a path
        return {'_resolve':True}
    # this happens with "foo::"->['foo','']
    elif t[1]=='':
        #This is the same as build everything
        if t[0] in ['name','alias']:
            return {'all':True}
        else:
            return {'concept':t[0],'all':True}
    # this is the case of foo::xxx
    else:
        # Pasre the value (xxx part)
        tmp=t[1].split(seperator)
        if len(tmp) == 1:
            # here we have the case of <concept>::<value>
            # we need to figure out is this is name::xxx, alias::xxx or concept:xxx
            if t[0] == 'name':
                #it is equal to name, this means the concept is the default
                # ie the name::foo@key:val
                # set the name concept to None
                _concept=None
            elif t[0] == 'alias':
                #it is equal to alias, this means the concept is the default
                # ie the alias::foo
                return {'concept':None,'alias':tmp[0]}
            else:
                # we have some concept. the utest::foo@key:value case
                _concept=t[0]
            
            # given we a name.. figure out what part properties to match on have been added
            # see if this has a version value given to it as well
            tmp=t[1].split('@')
            if len(tmp)==1:
                # have no meta value to test for
                return {'concept':_concept,'name':tmp[0]}
            #we have meta values
            # loop and seperate them in to a dictionary
            name=tmp[0]
            properties={}
            
            for p in tmp[1:]:
                
                try:
                    k,v=p.split(":")
                    properties[k]=v
                except ValueError:
                    reporter.report_error('target value "%s" is bad, @property "%s" not splitable by ":"'%(target,p))    
                
                
                
            return {'concept':_concept,'name':name,'properties':properties}
        
        elif tmp[1]=='':
            # <concept>::name:: or <concept>::alias:: like case
            _concept=t[0]
            if tmp[0] in ['alias','name']:
                return {'concept':_concept,'all':True}
            else:
                # bad value given that we are going to treat
                # <concept>::name or <concept>::alias as the same as <concept>::
                # this is soemthing else which we don't understand at the moment
                reporter.report_error('target value "%s" is bad'%(target))
                
        elif tmp[1]!='':
            # this is our concept
            _concept=t[0]
            # we need to reparse this as it could be something like
            # concept::alias::foo or concept::name::foo_1.2 ( second case is impiled)
            tmp=_parse_target(t[1])
            tmp.update({'concept':_concept})
            return tmp
        else:
            #error to many :: breaks
            reporter.report_error('target value "%s" as to make seperators "%s"'%(target,seperator))
            
_target_type_cache={}

'''
target_type is a class that allow a quick parsing to allow one to figureout if
the target string part alias or Scons alias. it allow in the case of parts for
one to see what concept, part object, and section/concept we want to process
'''
class target_type(object):
    def __init__(self,target):
        target=str(target)
        try:
            # this does not work...
            #self=_target_type_cache[target]
            # this does
            self.__dict__=_target_type_cache[target].__dict__
        except KeyError:            
            self.concept=None
            self.alias=None
            self.name=None
            self.properties={}
            self.all=False
            self._resolve=False # if true we need to resolve the value to see if this is a part based target or SCons based one
            self.orginal_string=target
            self.__dict__.update(_parse_target(target))
            _target_type_cache[target]=self
            
    @property
    def isPartAlias(self):
        ''' This property tells if the string is a Parts alias
        
        If this is False we assume it some type of SCons alias
        '''
        if self.concept is not None or\
            self.alias is not None or\
            self.name is not None or\
            self.all != False:
            return True
        else:
            return False
    
    def root_alias(self):
        if self.alias:
            return self.alias.split('.',1)[0]
        return None

    def root_name(self):
        if self.name:
            return self.name.split('.',1)[0]
        return None


