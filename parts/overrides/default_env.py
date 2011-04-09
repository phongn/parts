# this fix allows us to share setting with the default environment better
# this allows for better integration with SCons from the user point of view

from .. import glb
from .. import settings

import SCons.Script

scons_DefaultEnvironment=SCons.Script.DefaultEnvironment

def Part_DefaultEnvironment(*args,**kw):
        env=settings.DefaultSettings().DefaultEnvironment()#*args,**kw)
        glb.engine.def_env=env
        return env
        

SCons.Script.DefaultEnvironment=Part_DefaultEnvironment