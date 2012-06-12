from parts.config import *

def map_default_version(env):
    return env['GXX_VERSION']

def post_process_func(env):
    try:
        env.AppendUnique(LINKFLAGS=['-B{0}'.format(env['BINUTILS'].INSTALL_ROOT)])
    except KeyError:
        pass

config = configuration(map_default_version, post_process_func)

# vim: set et ts=4 sw=4 ai :

