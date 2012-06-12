#Stub file to update env for ar tool

import SCons.Tool.ar
import parts.tools.GnuCommon.binutils

def generate(env):
    parts.tools.GnuCommon.binutils.setup(env)

    SCons.Tool.ar.generate(env)

def exists(env):
    parts.tools.GnuCommon.binutils.setup(env)

    return SCons.Tool.ar.exists(env)

# vim: set et ts=4 sw=4 ai ft=python :

