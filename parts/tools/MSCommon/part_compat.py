
##This file contains functions in parts that add concepts not currently in SCons
##Instead of making two version of the new MS tools i just wrappered some shared code
##to be add for compatibility and to make my life easier, Hopefully SCons will 
##add objects like these in the future to SCons 
import SCons.Platform

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
    
    
