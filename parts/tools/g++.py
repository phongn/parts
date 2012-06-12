
import SCons.Util
import SCons.Tool
import parts.tools.GnuCommon

# have to copy this file from Scons as I can't seem to get the import to get it from the standad SCons install
cplusplus = __import__('c++', globals(), locals(), [])

import parts.api.output as output

def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # get the basic C++ flags (unix based stuff only??)
    cplusplus.generate(env)

    # set up shell env for running compiler
    parts.tools.GnuCommon.gxx.MergeShellEnv(env)

    env['CXX'] = env['GXX']['TOOL']

    # platform specific settings
    # don't mess with these
    if env['PLATFORM'] == 'aix':
        env['SHCXXFLAGS'] = SCons.Util.CLVar('$CXXFLAGS -mminimal-toc')
        env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1
        env['SHOBJSUFFIX'] = '$OBJSUFFIX'
    else:
        env['SHOBJSUFFIX'] = '.pic.o'
        env['OBJSUFFIX'] = '.o'
    
    #Backward compatiblity
    env['CXXVERSION']=env['GXX']['VERSION']  
    
    # this is a hack to deal with some migration issues with cross builds and existing parts files
    # this is to work around broken linux installs that can break cross building
    # with autoconfig via a Command() call.. or at least this helps
    if env['HOST_ARCH'] == 'x86' and env['TARGET_ARCH'] == 'x86_64':
        env['CXX']=env['CXX']+' -m64'
    elif env['HOST_ARCH'] == 'x86_64' and env['TARGET_ARCH'] == 'x86':
        env['CXX']=env['CXX']+' -m32'

 # fix this up so we can control its printing to screen better.
    #api.output.print_msg( "Configured Tool %s\t for version <%s> target <%s>"%('g++',env['GXX']['VERSION'],env['TARGET_PLATFORM']))


def exists(env):
    return parts.tools.GnuCommon.gxx.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
