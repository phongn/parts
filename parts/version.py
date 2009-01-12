import versionobject
import UserList


class version(versionobject.VersionObject):
    '''
    This is a wrapper wround the Version object Albert wrote. This limits the version
    object to that of a given version number. It also add basic operator overloads
    to make the object behave in a more natural way. I believe this makes the 
    object easier to use, over the orginal object Albert wrote which has a dual
    meaning.
    '''
    def __init__(self,major,minor=None,rev=None):
        vstr=''
        if isinstance(major,version):
            versionobject.VersionObject.__init__(self,major.ToString())
        elif major== None:
            versionobject.VersionObject.__init__(self,'None_0.0.0')
        else:
            vstr=str(major)
            if minor!=None:
                vstr+='.'+str(minor)
                if rev!=None:
                    vstr+='.'+str(rev)
            versionobject.VersionObject.__init__(self,vstr)
    
    def __str__(self):
        return self.ToString()
    
    def __sub__(self,rhs):
        if rhs==None:
            rhs='*'
        return version_range(self.ToString()+'-'+str(rhs))
    
    def __rsub__(self,lhs):
        if lhs==None:
            lhs='*'
        return version_range(str(lhs)+'-'+self.ToString())
    
    def __lt__(self,obj):
        if obj==None:
            return False
        return versionobject.CompareVersionNumbers(self.ToString(),str(obj))[1]==-1
    def __eq__(self,obj):
        if obj==None:
            return False
        return versionobject.CompareVersionNumbers(self.ToString(),str(obj))[1]==0
    def __gt__(self,obj):
        if obj==None:
            return True
        return versionobject.CompareVersionNumbers(self.ToString(),str(obj))[1]==1
    def __ge__(self,obj):
        if obj==None:
            return True
        return versionobject.CompareVersionNumbers(self.ToString(),str(obj))[1]>=0
    def __le__(self,obj):
        if obj==None:
            return False
        return versionobject.CompareVersionNumbers(self.ToString(),str(obj))[1]<=0

    
    # need to clean up orginal version objects code a bit to make this cleaner
    def major(self):
        ''' 
        Allows direct access to the major part of the version number
        '''
        err,maj,min,rev=versionobject.parseVersionNumber(self.ToString())
        return maj
    def minor(self):
        ''' 
        Allows direct access to the minor part of the version number
        '''
        err,maj,min,rev=versionobject.parseVersionNumber(self.ToString())
        return min
    def revision(self):
        ''' 
        Allows direct access to the revision part of the version number
        '''
        err,maj,min,rev=versionobject.parseVersionNumber(self.ToString())
        return rev
    def short_version_string(self):
        ''' 
        returns a short version of the version number as a string. Ie instead of
        1.2.3 you get 1.2
        '''
        err,maj,min,rev=versionobject.parseVersionNumber(self.ToString())
        return str(maj)+'.'+str(min)

class version_range(versionobject.VersionObject):
    ''' 
    This is a wrapper wround the Version object Albert wrote, but it limits 
    the use to be that of a range, not an exact version. I believe this will
    help clarify useage, over what I think become confusng with what Albert
    tried to do.
    '''
    def __init__(self,include,exclude=None):
        rstr=''
        if isinstance(include,version_range) or isinstance(include,version):
            rstr=include.ToString()
        elif type(include) is type(''):
            rstr=include
        elif include is type([]) or isinstance(include,UserList.UserList):
            for i in include:
                if isinstance(i,version_range):
                    rstr+=i.ToString()+','
                elif i is type(''):
                    rstr+=include+','
                elif isinstance(i,version):
                    rstr+=str(i)+','
        else:
            rstr='None_0.0.0'
        if exclude != None:
            if include != None:
                rstr = ''
            if isinstance(exclude,version_range):
                rstr=exclude.ToString()
            elif exclude is type(''):
                rstr=exclude
            elif type(include) is type([]) or isinstance(obj,UserList.UserList):
                for i in include:
                    if isinstance(i,version_range):
                        rstr+='!'+i.ToString()+','
                    elif i is type(''):
                        rstr+='!'+include+','
                    elif isinstance(i,version):
                        rstr+='!'+str(i)+','
                    
        versionobject.VersionObject.__init__(self,rstr)
    
    def __str__(self):
        return self.ToString()
    def __contains__ (self,item):
        #print version(item),self.ToString(),self.Match(version(item))
        return self.Match(version(item))

if __name__ != '__main__':
# This is what we want to be setup in parts
    from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
    SConsEnvironment.Version=version
    SConsEnvironment.VersionRange=version_range




# this is just a simple test to validate the code
if __name__ == '__main__':
    v1=version(1,2,3)
    v2=version(1)
    v3=version('2.0')
    v4=version(v1)
    
    print v1
    print v2
    print v3
    print v4
    
    print v2-v3
    print v2-'2.0'
    print '1'-v3
    
    print v1 in v2-v3
    print v1 in v2-'2.0'
    print v1 in '1'-v3
    print v1 in version_range('1-2.0')
    
    print version_range('1-2.0')
    print version_range('2.0')
    print version_range('2.0.0')
    print version_range(None)
    print None in version_range(None)
    
    print '7' in version_range('7.1.0'),"should be false"
    print '7' in version_range('7.0-8.0'),"should be true"
    print '8.3' in version_range('7.0-7.*'),"should be false"
    print version('8.3') in version_range('7.0-7.*'),"should be false"
    print '7.3.0' in version_range('7.0-7.2.*'),"should be false"
    print version('7.3.0') in version_range('7.0-7.2.*'),"should be false"
    
    print '6.0' in version_range('7.1-7.*'),"should be false"
    print version('7.0') in version_range('7.1-7.*'),"should be false"
    print '7.0.0' in version_range('7.1-7.2.*'),"should be false"
    print version('7.0.0') in version_range('7.1-7.2.*'),"should be false"
    print '7.2' in version_range('7.1-7.*'),"should be True"
    print version('7.2') in version_range('7.1-7.*'),"should be True"
    print '7.2' in version_range('7.*-7.1'),"should be false"
    print version('7.2') in version_range('7.*-7.1'),"should be false"
    
    print '8.0' in version_range('7.1-7.*'),"should be false"
    print version('8.0') in version_range('7.1-7.*'),"should be false"
    print '7.5' in version_range('7.1-7.2.*'),"should be false"
    print version('7.5.0') in version_range('7.1-7.2.*'),"should be false"
    print version('1.5.0') in version_range('1.1-*.*')
    print version('2.5.0') in version_range('1.1-*.*')
    

