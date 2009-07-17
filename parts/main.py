

#########################################################
### This is the init code that make every start correctly.
###
# import main code
import env_overrides
import common 
import startup
import parts
import version

# import extra funcion 
## this will be viewed as global function to the user in the Sconstruct file
globals().update(common.g_globals)

### import the pieces
import pieces

# start up logic ... runs during import of the code
startup.start() # sets up everything