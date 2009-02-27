'''
Contains basic functions needed to provide bitness of OS and architecture
These function provide information on the current running platform.
User should not need these much, but it can be useful. With cross plaform support
added some day this will not be needed external, but instead user will use env 
var defined to to tell what has been targeted as the build env.
'''
import common
import SCons.Platform

def OSBit():
    ''' 
        OSBit
        
        returns the Scons os bit type
        This is important if you have a 64-bit chip but a 32-bit OS
        in this case you often can't or don't want to compile as a 64-bit
        application.
    '''
    import platform
    val = platform.architecture()[0]
    if val[-3:] == 'bit':
        val=val[:-3]
    return int(val)
    
        
def ChipArchitecture():
    ''' 
        ChipArchitecture
        
        returns the chip archecture
        Returns High level value for the archecture being used
        which is often more useful. Knowing if you have a 
        ia32, x64, ia64 in general is more intertesting
        than know if it is an P3 or P4
        
        x86 -- Intel(r) line of compatible 32-bit chips 
        x86_64 -- The 64-bit extended memory form of x86 (AMD64 or em64t)
        ia64 -- 
    
        # to add other system here
        
    '''
    arch_map = {
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
    #if win32
    import sys
    if sys.platform == 'win32':
        import os
        val=os.environ.get('PROCESSOR_ARCHITEW6432','')
        if val=='':
            val=os.environ['PROCESSOR_ARCHITECTURE']
        return arch_map.get(val,'')
    
    #else we just assume the python code will work at this time
    else:
        import platform
        return arch_map.get(platform.machine(),'')


class system_config:
    def __init__(self,platform=SCons.Platform.platform_default(),arch=ChipArchitecture()):
        self.platform=platform
        self.arch=arch
    
    def __eq__ (self,rhs):
        return self.platform==rhs.platform and self.arch == rhs.arch
    
    def __str__(self):
        return self.platform+"-"+self.arch
    
    def __hash__(self):
        return hash(str(self))
    
    def Architecture(self):
        return self.arch
    
    def Platform(self):
        return self.platform

_host_sys=system_config()
    
def HostSystem():
    return _host_sys

# add configuartion varaible
common.add_config_var('ARCHITECTURE',ChipArchitecture())
common.add_config_var('OSBITNESS',str(OSBit()))

common.add_config_var('HOST_SYSTEM',_host_sys)
common.add_config_var('TARGET_SYSTEM',_host_sys)

common.add_parts_object('ChipArchitecture',ChipArchitecture)
common.add_parts_object('OSBit',OSBit)
common.add_parts_object('HostSystem',HostSystem)
