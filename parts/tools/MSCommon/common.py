import os
import SCons.Util
from parts.tools.Common.ToolSetting import ToolSetting
import parts.platform_info 
from parts.tools.Common.Finders import RegFinder

logfile = os.environ.get('SCONS_MSCOMMON_DEBUG')
if logfile:
    try:
        import logging
    except ImportError:
        debug = lambda x: open(logfile, 'a').write(x + '\n')
    else:
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
        debug = logging.debug
else:
    debug = lambda x: None


def is_win64():
    """Return true if running on windows 64-bits OS."""
    return parts.platform_info.OSBit()==64

def read_reg(value):
    return SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)[0]


def framework_root():
    try:
        return framework_root.cache
    except AttributeError:
        r=RegFinder([
                'SOFTWARE\\Wow6432Node\\Microsoft\\VisualStudio\\SxS\\VC7\\FrameworkDir32',
                'SOFTWARE\\Microsoft\\VisualStudio\\SxS\\VC7\\FrameworkDir32'
                    ])
        r2=RegFinder([
                'SOFTWARE\\Wow6432Node\\Microsoft\\.NETFramework\\InstallRoot',
                'SOFTWARE\\Microsoft\\.NETFramework\\InstallRoot'
                    ])
        dir=r()
        if dir is None:
            dir=r2()
            if os.path.exists(dir) == False:
                 return ''
        framework_root.cache=dir
        return framework_root.cache
        
def framework_root64():
    ''' currently this value when added seem to be messed up in the scripts
    on 32-bit OS systems. Since this path is always bad, we don't add it in these
    cases'''
    
    try:
        return framework_root64.cache
    except AttributeError:
        r=RegFinder([
                'SOFTWARE\\Wow6432Node\\Microsoft\\VisualStudio\\SxS\\VC7\\FrameworkDir64',
                'SOFTWARE\\Microsoft\\VisualStudio\\SxS\\VC7\\FrameworkDir64'
                    ])
        r2=RegFinder([
                'SOFTWARE\\Wow6432Node\\Microsoft\\.NETFramework\\InstallRoot',
                'SOFTWARE\\Microsoft\\.NETFramework\\InstallRoot'
                    ])
        dir=r()
        if dir is None:
            dir=r2()
            if dir[-3:] != '64\\':
             dir=dir[:-1]+'64\\'
             if os.path.exists(dir) == False:
                 return ''
        framework_root64.cache=dir
        return framework_root64.cache

def validate_vars(env):
    """Validate the PCH and PCHSTOP construction variables."""
    if env.has_key('PCH') and env['PCH']:
        if not env.has_key('PCHSTOP'):
            raise SCons.Errors.UserError, "The PCHSTOP construction must be defined if PCH is defined."
        if not SCons.Util.is_String(env['PCHSTOP']):
            raise SCons.Errors.UserError, "The PCHSTOP construction variable must be a string: %r"%env['PCHSTOP']

#VC teh compiler and related tools
msvc=ToolSetting('MSVC')
# Microsft SDK (Platform)
mssdk=ToolSetting('MSSDK')
# Microsoft VS integration SDK (VSIP)
vssdk=ToolSetting('VSSDK')