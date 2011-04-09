"""SCons.Tool.link

Tool-specific initialization for the generic Posix linker.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008 The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "src/engine/SCons/Tool/link.py 3842 2008/12/20 22:59:52 scons"

import SCons.Defaults
import SCons.Tool
import SCons.Util
import SCons.Warnings
import SCons.Action

from SCons.Tool.FortranCommon import isfortran

cplusplus = __import__('c++', globals(), locals(), [])

issued_mixed_link_warning = False

def smart_link(source, target, env, for_signature):
    has_cplusplus = cplusplus.iscplusplus(source)
    has_fortran = isfortran(env, source)
    if has_cplusplus and has_fortran:
        global issued_mixed_link_warning
        if not issued_mixed_link_warning:
            msg = "Using $CXX to link Fortran and C++ code together.\n\t" + \
              "This may generate a buggy executable if the %s\n\t" + \
              "compiler does not know how to deal with Fortran runtimes."
            SCons.Warnings.warn(SCons.Warnings.FortranCxxMixWarning,
                                msg % repr(env.subst('$CXX')))
            issued_mixed_link_warning = True
        return '$CXX'
    elif has_fortran:
        return '$FORTRAN'
    elif has_cplusplus:
        return '$CXX'
    return '$CC'

##def shlib_emitter(target, source, env):
##    for tgt in target:
##        tgt.attributes.shared = 1
##    return (target, source)

shlinkAction = SCons.Action.Action('$SHLINK -o $TARGET $SHLINKFLAGS $SOURCES $_LIBDIRFLAGS $_LIBFLAGS')
linkAction = SCons.Action.Action('$LINK -o $TARGET $LINKFLAGS $SOURCES $_LIBDIRFLAGS $_LIBFLAGS')

# We define two classes PdbAction and StripAction
# The classes inherit from CommandAction and override
# only execute method. They perform actions only when
# PDB key is present in env or when NO_STRIP key is
# absent in env.
class PdbAction(SCons.Action.CommandAction):
    def execute(self,target,source,env):
        return 0
        if env.get('PDB'):
            return SCons.Action.CommandAction.execute(self,target,source,env)
        return 0

class StripAction(SCons.Action.CommandAction):
    def execute(self,target,source,env):
        return 0
        if env.get('PDB') or not env.get('NO_STRIP', True):
            return SCons.Action.CommandAction.execute(self,target,source,env)
        return 0

### The following two functions are used to inform user
### about what is going on here
##def pdbString(target, source, env):
##    if env.get('PDB'):
##        return "Creating PDB for %s" % target[0]
##    else:
##        return ""
##
##def stripString(target, source, env):
##    if env.get('PDB') or not env.get('NO_STRIP', True):
##        return "Stripping %s" % target[0]
##    else:
##        return ""
##
### Actions to be appended to Program and SharedLibrary builders
##stripActions = [
##    PdbAction("objcopy --only-keep-debug ${TARGETS[0]} ${TARGETS[1]}", strfunction = pdbString),
##    StripAction("objcopy --strip-unneeded ${TARGETS[0]}", strfunction = stripString),
##    PdbAction("objcopy --add-gnu-debuglink=${TARGETS[1]} ${TARGETS[0]}", strfunction = lambda x,y,z: "")
##]
##
### Emitter to generate *.pdb File node
##def pdbEmitter(target, source, env):
##    if env.get('PDB') and len(target)==1:
##        pdb = env.arg2nodes('$PDB', target=target, source=source)[0]
##        pdb.attributes.FilterAs = target[0]
##        target.append(pdb)
##    return target, source


def generate(env):
    """Add Builders and construction variables for gnulink to an Environment."""
    
    global shlinkAction
    global linkAction
    SCons.Tool.createSharedLibBuilder(env)
    SCons.Tool.createProgBuilder(env)


    env['SHLINK']      = '$LINK'
    env['SHLINKFLAGS'] = SCons.Util.CLVar('$LINKFLAGS -shared')
    env['SHLINKCOM']   = shlinkAction
    # don't set up the emitter, cause AppendUnique will generate a list
    # starting with None :-(
    #env.Append(SHLIBEMITTER = [shlib_emitter])
    env['SMARTLINK']   = smart_link
    env['LINK']        = "$SMARTLINK"
    env['LINKFLAGS']   = SCons.Util.CLVar('')
    env['LINKCOM']     = linkAction

##    if env.Detect('objcopy'):
##        env.Append(LINKCOM = stripActions)
##        env.Append(PROGEMITTER = [pdbEmitter])
##        env.Append(SHLINKCOM = stripActions)
##        env.Append(SHLIBEMITTER = [pdbEmitter])

    env['LIBDIRPREFIX']='-L'
    env['LIBDIRSUFFIX']=''
    env['_LIBFLAGS']='${_stripixes(LIBLINKPREFIX, LIBS, LIBLINKSUFFIX, LIBPREFIXES, LIBSUFFIXES, __env__)}'
    env['LIBLINKPREFIX']='-l'
    env['LIBLINKSUFFIX']=''

    if env['PLATFORM'] == 'hpux':
        env['SHLIBSUFFIX'] = '.sl'
    elif env['PLATFORM'] == 'aix':
        env['SHLIBSUFFIX'] = '.a'

    # For most platforms, a loadable module is the same as a shared
    # library.  Platforms which are different can override these, but
    # setting them the same means that LoadableModule works everywhere.
    SCons.Tool.createLoadableModuleBuilder(env)
    env['LDMODULE'] = '$SHLINK'
    env['LDMODULEPREFIX'] = '$SHLIBPREFIX' 
    env['LDMODULESUFFIX'] = '$SHLIBSUFFIX' 
    env['LDMODULEFLAGS'] = '$SHLINKFLAGS'
    env['LDMODULECOM'] = '$SHLINKCOM'



def exists(env):
    # This module isn't really a Tool on its own, it's common logic for
    # other linkers.
    return None
