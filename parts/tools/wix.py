import SCons.Defaults

from parts.api import output
from parts.tools.MSCommon.wix import wix
from parts.tools.MSCommon.wix import createWixObjectBuilder
from parts.tools.MSCommon.wix import createMsiBuilder

def generate(env):

    wixObject = createWixObjectBuilder(env)
    msi = createMsiBuilder(env)

    env['WIXCLCOM'] = '$WIXCL $WIXCLFLAGS -o $TARGET $SOURCE'

    env['WIXOBJPREFIX'] = ''
    env['WIXOBJSUFFIX'] = '.wixobj'
    env['WIXLINKEXTPREFIX'] = ''
    env['WIXLINKEXTSUFFIX'] = '.dll'
    env['_nodes_to_strs'] = lambda prefix, list, suffix, env: [str(x) for x in SCons.Defaults._concat_ixes(prefix, list, suffix, env)]
    env['_WIXEXTSTRS'] = '${_nodes_to_strs(WIXLINKEXTPREFIX, WIXLINKEXTENSIONS, WIXLINKEXTSUFFIX, __env__)}'
    env['_WIXLINKEXTENSIONS'] = '${_defines("-ext ", _WIXEXTSTRS, "", __env__)}'

    env['WIXFILEPATH'] = ['$SRC_DIR']
    env['WIXFILEDIRPREFIX'] = '-b ' # Do not remove trailing space
    env['WIXFILEDIRSUFFIX'] = ''
    env['_WIXFILEDIRFLAGS'] = '$( ${_concat(WIXFILEDIRPREFIX, WIXFILEPATH, WIXFILEDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['WIXLINKCOM'] = '$WIXLINK $WIXLINKFLAGS $_WIXLINKEXTENSIONS $_WIXFILEDIRFLAGS -o $TARGET $SOURCES'

    env['MSIPREFIX'] = ''
    env['MSISUFFIX'] = '.msi'

    wix.MergeShellEnv(env)
    env['WIXCL'] = env.Detect('candle')
    env['WIXLINK'] = env.Detect('light')

    output.print_msg(env.subst('Configured WiX tools of version ${WIX.VERSION} for target ${TARGET_PLATFORM}'))

def exists(env):
    return wix.Exists(env)

# vim: set et ts=4 sw=4 ft=python :

