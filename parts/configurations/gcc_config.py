######################################
### GCC compiler configurations
######################################

from parts.config_base import *
from parts.config import *

      
def GCC_tool_add(map,tool,ver,config):
    print "hello"
    map['tools']=['gcc']
    return True


# these seem like good defaults
gcc_setting_debug=['-O0', '-g']
gcc_setting_release=['-O2']

gcc_setting_debug64=['-O0', '-g','-m64']
gcc_setting_release64=['-O2','-m64']
gcc_link_setting_debug64= platform_link_flags_debug+['-m64']
gcc_link_setting_release64= platform_link_flags_release +['-m64']

configuration('release','gcc64',None,GCC_tool_add,LINKFLAGS= gcc_link_setting_release64,
              CCFLAGS=gcc_setting_release64,ASFLAGS=['-m64'],CC='gcc',CXX='g++')
configuration('debug','gcc64',None,GCC_tool_add,LINKFLAGS= gcc_link_setting_debug64,
              CCFLAGS=gcc_setting_debug64,ASFLAGS=['-m64'],CC='gcc',CXX='g++')


# the GCC compiler
## so it seem like there is no good convention yet for GCC and selecting different compilers
## Should look at this later
configuration('release','gcc',None,LINKFLAGS=platform_link_flags_release,
              CCFLAGS=gcc_setting_release)
configuration('debug','gcc',None,LINKFLAGS=platform_link_flags_debug,
              CCFLAGS=gcc_setting_debug)
   

