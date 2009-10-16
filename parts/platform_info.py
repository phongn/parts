'''
Contains basic functions needed to provide bitness of OS and architecture
These function provide information on the current running platform.
User should not need these much, but it can be useful. With cross plaform support
added some day this will not be needed external, but instead user will use env 
var defined to to tell what has been targeted as the build env.
'''
import common
import SCons.Platform
import env_overrides
import os,sys

def OSBit():
    ''' 
        OSBit
        
        returns the Scons os bit type
        This is important if you have a 64-bit chip but a 32-bit OS
        in this case you often can't or don't want to compile as a 64-bit
        application.
    '''
    import platform
        
    # Unfortunately, python does not provide any way to tell if the OS itself
    # is 32-bit or 64-bit. What is worse is that 32-bit vs 64-bit python effects
    # the value Python might return. This tell us nothing of the current system
    # The test below returns
    if sys.platform == 'win32':
        # this test fails on server 2008
        # may fail on window 7 ( don't know yet)
        value = "Software\Wow6432Node"
        ret=None
        try:
            ret = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)
        except:
            pass
        if ret is None and os.environ.get('PROCESSOR_ARCHITEW6432',None) is None:
            return 32
        else:
            return 64
    #assume is is correct. ## test later the  getconf LONG_BIT command
    val = platform.architecture()[0]
    if val[-3:] == 'bit':
        val=val[:-3]
    return int(val)
    
def MapArchitecture(val):
    ''' 
    Maps the value of lowlevel architures to high level one that
    are more generic and useful.
    
    supported currently
        x86 -- Intel(r) line of compatible 32-bit chips 
        x86_64 -- The 64-bit extended memory form of x86 (AMD64 or em64t)
        ia64 -- 
    
        # to add other system here    
    '''
    arch_map = {
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
    'ia64':'ia64'
    }
    return arch_map.get(val,'')
        
def ChipArchitecture():
    ''' 
        ChipArchitecture
        
        returns the chip archecture
        Returns High level value for the archecture being used
        which is often more useful. Knowing if you have a 
        ia32, x64, ia64 in general is more intertesting
        than know if it is an P3 or P4
        
    '''
    #if win32
    import sys
    if sys.platform == 'win32':
        import os
        val=os.environ.get('PROCESSOR_ARCHITEW6432','')
        if val=='':
            val=os.environ['PROCESSOR_ARCHITECTURE']
        return MapArchitecture(val)
    
    #else we just assume the python code will work at this time
    else:
        import platform
        return MapArchitecture(platform.machine()) 


class SystemPlatform(env_overrides.bindable):
    def __init__(self,os=SCons.Platform.platform_default(),arch=ChipArchitecture()):
            
        self.key="_parts_"
        self._env={
                self.key+"_OS":os,
                self.key+"_ARCH":arch
            }
        
    def _getOS(self):
        return self._env[self.key+"_OS"]

    def _setOS(self, x):
        self._env[self.key+"_OS"]= x
        
    def _getArch(self):
        return self._env[self.key+"_ARCH"]

    def _setArch(self, x):
        self._env[self.key+"_ARCH"]= x        
        
    ARCH = property(_getArch,_setArch)
    OS = property(_getOS,_setOS)

    def _bind(self,env,key):
        # this is a bit of a hack to forward stuff in SCons as it should be in 1.3
        if key == "TARGET_PLATFORM" or key == "HOST_PLATFORM":
            tkey = key[:-9]
            env[tkey+"_ARCH"] = self.ARCH != 'any' and self.ARCH or env.has_key(tkey+"_ARCH") and env[tkey+"_ARCH"] or ChipArchitecture() # getArch
            env[tkey+"_OS"]= self.OS != 'any' and self.OS or env.has_key(tkey+"_OS") and env[tkey+"_OS"] or SCons.Platform.platform_default() # getPlatform
            self.key=tkey
            self._env=env
        
    def _rebind(self,env,key):
        tmp=SystemPlatform(os=self.OS,arch=self.ARCH)
        tmp._bind(env,key)
        return tmp

    def __eq__ (self,rhs):
        if common.is_string(rhs):
            rhs=target_convert(rhs,base=self)
            
        return (self.OS==rhs.OS or\
                'any'==rhs.OS or\
                'any'==self.OS) and\
            (self.ARCH==rhs.ARCH or\
                'any'==rhs.ARCH or\
                'any'==self.ARCH)
                
    def __ne__ (self,rhs):
        return (not self.__eq__(rhs))

    def __str__(self):
        return self.OS+"-"+self.ARCH
    
    def __repr__(self):
        return self.OS+"-"+self.ARCH
    
    def __hash__(self):
        return hash(str(self))

    def _is_native(self):
        return 'any'!= self.OS and 'any' != self.ARCH 
    
    #because of the mapping to ENV we have to do our own copy
    def __copy__(self):
        return SystemPlatform(self.OS,self.ARCH)
    
    def __deepcopy__(self):
        return SystemPlatform(self.OS,self.ARCH)
    
    def __getitem__(self, key):
        return self.__class__.__dict__[key.upper()].fget(self)
    
    def __setitem__(self, key,val):
        if self.__class__.__dict__.has_key(key.upper()) == False:
            raise KeyError('SystemPlatform has no member '+key.upper())
        self.__class__.__dict__[key.upper()].fset(self,val)
            

_host_sys=SystemPlatform()
    
def HostSystem():
    return _host_sys

def target_convert(str_val, raw_val=None,base=None):
    host_sys= base is None and _host_sys or base
    lst=str_val.split('-')
    if len(lst) > 2:
        raise ValueError("Warning:  %s is not a valid target_system value\nValue must be in form of <Plaform>-<Architecture>" % o)
    if len(lst) == 1:
        # nice to a have short cut
        tmp=MapArchitecture(lst[0])
        if tmp == '':
            #assume this was a platform
            ret=SystemPlatform(
                lst[0],host_sys.ARCH
                )
        else:
            #assume this is a architure
            ret=SystemPlatform(
                    host_sys.OS,lst[0]
                    )
    else:
        p=lst[0]
        a=lst[1]
        if p == '':
            p=host_sys.OS
        if a == '':
            a=host_sys.ARCH
        ret=SystemPlatform(p,a)
    return ret

# add configuartion varaible
common.AddVariable('OSBITNESS',str(OSBit()),'to be removed??')

common.AddVariable(['TARGET_PLATFORM','target_platform','target'],SystemPlatform(_host_sys.OS,_host_sys.ARCH), 
        'Value of what to type of system to target build for, used to control cross builds',
        converter=target_convert)

common.add_parts_object('ChipArchitecture',ChipArchitecture)
common.add_parts_object('OSBit',OSBit)
#common.add_parts_object('Host_Platform',HostSystem)

common.add_global_value('ChipArchitecture',ChipArchitecture)
common.add_global_value('OSBit',OSBit)
common.add_global_value('HostPlatform',HostSystem)
common.add_global_value('SystemPlatform',SystemPlatform)


