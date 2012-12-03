
import SCons.Util
import SCons.Tool.cc
import parts.tools.GnuCommon
import parts.tools.Common
import parts.api.output as output

def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    SCons.Tool.cc.generate(env)
    
    # set up shell env for running compiler
    parts.tools.GnuCommon.gcc.MergeShellEnv(env)
    env['CC'] = parts.tools.Common.toolvar(env['GCC']['TOOL'],('gcc','gnu'))

   # this setting is what SCons has.. It seem odd, I thought cygwin handled -fpic fine
    if env['PLATFORM'] in ['cygwin', 'win32']:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS')
    else:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')

    #Backward compatiblity
    env['CCVERSION']=env['GCC']['VERSION']
        
    env['SHOBJSUFFIX'] = '.pic.o'
    env['OBJSUFFIX'] = '.o'

 # fix this up so we can control its printing to screen better.
    #api.output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('gcc',env['GCC']['VERSION'],env['TARGET_PLATFORM']))
        
    

def exists(env):
    return parts.tools.GnuCommon.gcc.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:


