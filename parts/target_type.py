import glb
import common
import api.output

from SCons.Debug import logInstanceCreation

# move to glb once we have new formats working
__known_concepts={
'utest':'utest',
'run_utest':'utest',
'build':'build'
}

def is_concepts(val):
    return val in __known_concepts

def map_concept(val):
    return __known_concepts[val]


def get_concept(tlst):
    # see if the concept is defined

    # special 'all' case
    if tlst[0]=='all' and len(tlst) == 1:
        return {'_section':'build','_recursive': True},tlst[1:]
    # special case that is possibly ambiguous'
    if len(tlst) == 1 and "@" not in tlst[0]:
        return {'_section':'build','_recursive': False,'_ambiguous':True,'_name':tlst[0]},tlst[1:]
    # special case of "alias:: or name::
    if len(tlst)==2 and tlst[0] in ['name','alias'] and tlst[1]=='':
        return {'_section':'build'},tlst[1:]
    # some concept would have to be xxx:: else we assume it is a name
    elif is_concepts(tlst[0]) and len(tlst) > 1:
        #we have a concept defined
        section=map_concept(tlst[0])
        return {'_concept':tlst[0],'_section':section},tlst[1:]

    # set default concept
    # value is hard coded at the moment
    return {'_section':'build'},tlst


def get_partrefdata(tok):

    if not tok:
        return {},tok
    # <concpet>::
    elif len(tok) == 1 and tok[0] == '':
        return {},tok
    # alias
    elif tok[0] == 'alias' and len(tok) == 1:
        return get_name(tok)
    #alias::??
    elif tok[0] == 'alias':
        return get_alias(tok[1:])
    # name or name@k,v...
    elif tok[0].startswith('name') and len(tok) == 1:
        return get_name(tok)
    #name::xxx
    elif tok[0] == 'name':
        return get_name(tok[1:])
    # xxx which we assume to be a name..
    elif tok[0] != '':
        return get_name(tok)
    #<concept>::::<group> or <concept>::::
    elif tok[0] == '':
        return {},tok[1:]
    else:
        1/0 # not sure if we can get here...


def get_alias(tok):

    #<concept>::alias:: same as concept::
    if len(tok) == 1 and tok[0] == '':
        return {},tok
    #<concept>::alias::::<group>
    elif tok[0] == '':
        return {},tok[1:]
    #<concept>::alias::<alias>
    else:
        return {'_alias':tok[0]},tok[1:]

def get_name(tok):

    #<concept>::name:: same as concept::
    if len(tok) == 1 and tok[0] == '':
        return {},tok
    #<concept>::name::::<group>
    elif tok[0] == '':
        return {},tok[1:]
    #name::@k,v
    elif tok[0].startswith('@'):
        tlst=tok[0].split("@")
        prop=get_properties(tlst[0])
        return {'_properties':prop},tok[1:]
    #name::XXX@k,v
    else:
        tlst=tok[0].split("@")
        prop=get_properties(tlst[1:])
        return {'_name':tlst[0],'_properties':prop},tok[1:]

def get_properties(tlst):
    properties={}
    for p in tlst:
        try:
            # get key value
            k,v=p.split(":")
            # break up value into list
            vtmp=v.split(',')
            # remove exta junk at end if it exists
            if vtmp[-1]=='':
                vtmp=vtmp[:-1]
            # set if we have a list as a list
            if len(vtmp) > 1:
                properties[k]=vtmp
            else:
                # else this is a simple value ( non list)
                properties[k]=v
        except ValueError:
            api.output.error_msg('target value "%s" is bad, @property "%s" not splitable by ":"'%(target,p))
    return properties

def get_groups(tlst):
    # end of the line
    if not tlst:
        return {},tlst
    # something like foo::::
    elif tlst[0] == '' and len(tlst) > 1:
        return {},tlst[1:]
    # something like foo::
    elif tlst[0] == '' and len(tlst) == 1:
        return {},tlst
    else:
        return {'_groups':tlst[0].split(',')},tlst[1:]


def _parse_target(target):
    '''
    Parses the Target to help Parts figure out how to treat the Target

    The current logic is to handle cases such as:
    \verbatim
        alias::<part_alias>
        <part name>
        name::<part name>
        name::<part name>@key:value
        name::<part name>@key:value@key2:val2 ...
        name::<part name>@key:vala,valb,valc@key2:val2 ...
        <concept>::<some form from above>
        <concept>::<some form from above>::
    \endverbatim
    '''


    seperator='::'
    # split in to major catagories
    t=target.split(seperator)
    ret={}
    # does this have to many breaks... This is the max given values such a
    # build::name::foo::group::
    # however a case of build:::::::: is also to many as no name is provided
    if len(t) > 5:
        api.output.error_msg('target value "%s" is bad, to many :: breaks":"'.format(target))
    # get the concept
    r,t=get_concept(t)
    ret.update(r)
    if not t:
        return ret
    # process reference data
    # returns a dict with values of all,alias,name,properties set
    r,t=get_partrefdata(t)
    ret.update(r)
    #process any groups
    r,t=get_groups(t)
    ret.update(r)
    #process the recurse
    if not t or t[0]!='':
        ret['_recursive']=False
    else:
        ret['_recursive']=True

    if len(t) > 1:
        api.output.error_msg('target value "%s" is bad, to many :: breaks":"'.format(target))
    return ret

_target_type_cache={}

'''
target_type is a class that allow a quick parsing to allow one to figureout if
the target string part alias or Scons alias. it allow in the case of parts for
one to see what concept, part object, and section/concept we want to process
'''
class target_type(object):
    def __init__(self,target):
        if __debug__: logInstanceCreation(self)
        target=str(target)
        try:
            # this does
            self.__dict__=_target_type_cache[target].__dict__.copy()
        except KeyError:
            self._concept=None
            self._section=None
            self._alias=None
            self._name=None
            self._recursive=False
            self._properties={}
            self._groups=[]
            self._ambiguous = False # if true we need to resolve the value to see if this is a part based target or SCons based one
            self._orginal_string=target
            self._recursive=False
            self.__dict__.update(_parse_target(target))
            #_target_type_cache[target]=self

    @property
    def Concept(self):
       return self._concept

    @Concept.setter
    def Concept(self,value):
       self._concept=value

    @property
    def hasConcept(self):
       return self._concept is not None

    @property
    def Section(self):
       return self._section

    @Section.setter
    def Section(self,value):
       self._section=value

    @property
    def hasSection(self):
       return self._section is not None

    @property
    def Alias(self):
       return self._alias

    @Alias.setter
    def Alias(self,value):
       self._alias=value

    @property
    def hasAlias(self):
       return self._alias is not None

    @property
    def Name(self):
       return self._name

    @Name.setter
    def Name(self,value):
       self._name=value

    @property
    def hasName(self):
       return self._name is not None

    @property
    def Properties(self):
       return self._properties

    @property
    def hasProperties(self):
       return self._properties == {}

    @property
    def OrignialString(self):
       return self._orginal_string

    @property
    def RootAlias(self):
        if self.hasAlias:
            return self.Alias.split('.',1)[0]
        return None

    @property
    def RootName(self):
        if self.hasName:
            return self.Name.split('.',1)[0]
        return None

    @property
    def Groups(self):
       return self._groups

    @property
    def hasGroups(self):
       return self._groups != []

    @property
    def isRecursive(self):
       return self._recursive

    @property
    def isAmbiguous (self):
        return self._ambiguous

    def setUnambiguous (self,value):
        self._ambiguous=False

    def __str__(self):
        '''
        Return a string form of target with any changed values.
        Use orginal_string value to get the orginal value used to Intially create this object
        '''
        s=''
        if self.hasConcept:
            s+="{0}::".format(self.Concept)
        if self.hasAlias:
            s+="alias::{0}".format(self.Alias)
        elif self.hasName:
            s+="name::{0}".format(self.Name)
            for k,v in self.Properties.iteritems():
                s+="@"+k+":"
                if common.is_list(v):
                    s+=",".join(map(str,v))
                else:
                    s+=str(v)
        elif self.hasConcept == False:
            s+="{0}::".format(self.Section)

        if self.hasGroups:
            s+="::"
            if len(self.Groups) > 1:
                s+=",".join(map(str,self.Groups))
            else:
                s+=str(self.Groups[0])
        if self.isRecursive and s.endswith("::") == False:
            s+="::"
        return s
