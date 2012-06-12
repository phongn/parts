######################################
### GNU linker configurations
######################################

from gnulink import config
from parts.config import ConfigValues

config.VersionRange("*",
                    prepend=ConfigValues(
                        LINKFLAGS=['-m64']
                        )
                    )

