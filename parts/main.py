

#########################################################
### This is the init code that make every start correctly.
###
# import main code
import common 
import startup
import parts
import version

# import extra funcion 
## this get viewed as global function to the user in the Sconstruct file
from parts import Part
from parts import Part as part
from startup import SetOptionDefault
from vcs import vcs_svn as VcsSvn
from vcs import vcs_cvs as VcsCvs
from vcs import vcs_Prebuilts as VcsPreBuilt
from core import parts_version_text as PartVersionString
from core import is_parts_version_beta as IsPartsExtensionVersionBeta
from core import PartsExtensionVersion as PartsExtensionVersion
from platform_info import ChipArchitecture as ChipArchitecture
from platform_info import OSBit as OSBit

### import the configurations
# this action does the dynamic load of a configurations
import configurations
import pieces


# start up logic ... runs during import of the code
startup.start() # sets up everything