#Stub file to update env for ar tool

#import SCons.Tool.as as AS
AS = __import__('SCons.Tool.as', globals(), locals(), [])
import parts.tools.GnuCommon.binutils
import parts.tools.Common

def generate(env):
    parts.tools.GnuCommon.binutils.setup(env)
    AS.generate(env)
    env['AS'] = parts.tools.Common.toolvar(env['AS'],('as'))

def exists(env):
    parts.tools.GnuCommon.binutils.setup(env)

    return AS.exists(env)

# vim: set et ts=4 sw=4 ai ft=python :

