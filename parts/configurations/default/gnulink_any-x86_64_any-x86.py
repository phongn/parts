######################################
### GNU linker configurations 
######################################

from gnulink import post_process_func,map_default_version
from parts.config import *

config = configuration(map_default_version, post_process_func)

config.VersionRange("*",
                    prepend=ConfigValues(
                        LINKFLAGS=['-m32']
                        )
                    )

