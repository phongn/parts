import os.path
import re
import subprocess

import SCons.Tool
import SCons.Util
import GnuCommon

# have to copy this file from Scons as I can't seem to get the import to get it from the standad SCons install
cplusplus = __import__('c++', globals(), locals(), [])


def generate(env):
    """Add Builders and construction variables for g++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    # get the basic C++ flags (unix based stuff only??)
    cplusplus.generate(env)

    # set up shell env for running compiler
    GnuCommon.gxx.MergeShellEnv(env)

    env['CXX'] = env['GXX']['TOOL']

    # platform specific settings
    # don't mess with these
    if env['PLATFORM'] == 'aix':
        env['SHCXXFLAGS'] = SCons.Util.CLVar('$CXXFLAGS -mminimal-toc')
        env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1
        env['SHOBJSUFFIX'] = '$OBJSUFFIX'
    elif env['PLATFORM'] == 'hpux':
        env['SHOBJSUFFIX'] = '.pic.o'
    elif env['PLATFORM'] == 'sunos':
        env['SHOBJSUFFIX'] = '.pic.o'
    

def exists(env):
    return GnuCommon.gxx.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
