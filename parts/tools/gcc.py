

import SCons.Tool.cc
import os
import re
import subprocess
import GnuCommon


def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    SCons.Tool.cc.generate(env)
    
    # set up shell env for running compiler
    GnuCommon.gcc.MergeShellEnv(env)

   # this setting is what SCons has.. It seem odd, I thought cygwin handled -fpic fine
    if env['PLATFORM'] in ['cygwin', 'win32']:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS')
    else:
        env['SHCCFLAGS'] = SCons.Util.CLVar('$CCFLAGS -fPIC')
    

def exists(env):
    return GnuCommon.gcc.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:


