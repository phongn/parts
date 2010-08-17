import common
import reporter

def _parse_target(target):
    '''
    we need to parse the target to get a clue of what parts to read if any
    '''
    if target is None:
        return {}
    seperator=common.g_engine.def_env.subst("$ALIAS_SEPARTATOR")
    t=target.split(seperator,1)   
    if len(t) == 1:
        # we have an part alias, SCons alias or a path
        # test to see if this is a part alias
        if common.g_engine._part_manager._from_alias(t[0]) is not None:
            # return state as alias
            return {'alias':t[0]}
        # test to see if it is a path
            # if so see if we can detect alias or name of part it might be part of
        else:
        # return that it some SCons alias
            return {}
        
    elif t[1]=='':
        #This is the same as build everything
        return {'concept':t[0],'all':True}
    else:
        tmp=t.split(seperator)
        if len(tmp) == 1:
            #we have a name
            #Figure out if this "concept" is a saying use a name
            if tmp[0]=='name':
                # it is equal to name, this means the concept is the default
                _concept=None
            else:
                _concept=tmp[0]
            # see if this has a version value given to it as well
            tmp=tmp.split('_',1)
            if len(tmp)==1:
                return {'concept':_concept,'name':tmp[0]}
            return {'concept':_concept,'name':tmp[0],'version':tmp[1]}
        elif tmp[1]=='':
            # utest::alias:: like case
            _concept=t[0]
            if tmp[0] in ['alias','name']:
                return {'concept':_concept,'all':True}
            else:
                # bad value
                reporter.report_error('target value "%s" is bad'%(target))
                
        elif tmp[1]!='':
            # this is our concept
            _concept=t[0]
            # we need to reparse this as it could be something like
            # concept::alias::foo or concept::name::foo_1.2 ( second case is impiled)
            tmp=parse_target(tmp[1])
            
            ret={'concept':_concept,'name':tmp[0],'version':tmp[1]}
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
        try:
            # this does not work...
            #self=_target_type_cache[target]
            # this does
            self.__dict__=_target_type_cache[target].__dict__
        except KeyError:            
            self.concept=None
            self.alias=None
            self.name=None
            self.version=None
            self.all=False
            self.orginal_string=target
            self.__dict__.update(_parse_target(target))
            _target_type_cache[target]=self
            
        
    def isPartAlias(self):
        if self.concept is not None or\
            self.alias is not None or\
            self.name is not None or\
            self.version is not None or\
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


