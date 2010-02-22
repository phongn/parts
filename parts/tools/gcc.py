
import SCons.Util
import SCons.Tool.cc
import GnuCommon

import parts.reporter as reporter

def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    SCons.Tool.cc.generate(env)
    
    # set up shell env for running compiler
    GnuCommon.gcc.MergeShellEnv(env)
    env['CC'] = env['GCC']['TOOL']

   # this setting is what SCons has.. It seem odd, I thought cygwin handled -fpic fine
    if env['PLATFORM'] in ['cygwin', 'win32']:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS')
    else:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')

    #Backward compatiblity
    env['CCVERSION']=env['GCC']['VERSION']
    
    # this is to work around broken linux installs that can break cross building
    # with autoconfig.. or at least this helps
    if env['HOST_ARCH'] == 'x86' and env['TARGET_ARCH'] == 'x86_64':
        env['CC']=env['CC']+' -m64'
    if env['HOST_ARCH'] == 'x86_64' and env['TARGET_ARCH'] == 'x86':
        env['CC']=env['CC']+' -m32'
    
 # fix this up so we can control its printing to screen better.
    reporter.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('gcc',env['GCC']['VERSION'],env['TARGET_PLATFORM']))
        
    

def exists(env):
    return GnuCommon.gcc.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:


