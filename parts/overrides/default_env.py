# this fix allows us to share setting with the default environment better
# this allows for better integration with SCons form the user point of view

from .. import poptions
from .. import common

import SCons.Script

scons_DefaultEnvironment=SCons.Script.DefaultEnvironment

def Part_DefaultEnvironment(*args,**kw):
    if common.g_engine is None or common.g_engine.def_env is None:
        return scons_DefaultEnvironment(*args,**kw)
    try:
        if poptions.SetOptionDefault._modified==False:
            return Part_DefaultEnvironment._cache
    except AttributeError:
        pass
    #remake the def env
    common.g_engine._setup_defenv()
    #store in chache
    Part_DefaultEnvironment._cache=common.g_engine.def_env
    poptions.SetOptionDefault._modified=False
    return Part_DefaultEnvironment._cache

SCons.Script.DefaultEnvironment=Part_DefaultEnvironment