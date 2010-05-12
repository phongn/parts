

#########################################################
### This is the init code that make every start correctly.
###
# import main code
import env_overrides
import common 
import parts
import version
import filters
import version_info
import installs

import engine

# create the engine
common.g_engine=engine.parts_addon()

### import the pieces
import pieces

# import extra funcion 
## this will be viewed as global function to the user in the Sconstruct file
globals().update(common.g_globals)

# start up logic ... runs during import of the code
common.g_engine.Start() # sets up everything

