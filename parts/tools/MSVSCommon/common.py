import SCons.Util

#try:
    #from logging import debug
#except ImportError:
#    debug = lambda x : None

def debug(x):
    #print "L",x
    pass

# this is basic cache of known data
FOUND_VC={
'x86':[],
'x86_64':[]
}

SUPPORTED_VERSIONS = [9.0, 8.0, 7.1, 7.0, 6.0]
SUPPORTED_VERSIONSSTR = [str(i) for i in SUPPORTED_VERSIONS]

VSCOMNTOOL_VARNAME = dict([(str(v), 'VS%dCOMNTOOLS' % round(v * 10))
                           for v in SUPPORTED_VERSIONS])


def is_win64():
    """Return true if running on windows 64-bits OS."""
    # Unfortunately, python does not provide any way to tell if the OS itself
    # is 32-bit or 64-bit. What is worse is that 32-bit vs 64-bit python effects
    # the value Python might return. This tell us nothing of the current system
    # The test below returns
    value = "Software\Wow6432Node"
    yo=None
    try:
        yo = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)
    except:
        pass
    if yo is None:
        return False
    else:
        return True

#print 'is win64',is_win64()

def read_reg(value):
    return SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)[0]

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

