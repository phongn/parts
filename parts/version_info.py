from parts_version import _PARTS_VERSION

import common

def parts_version_text():
    return 'Parts extension for SCons, Version '+_PARTS_VERSION

def parts_version_text_env(env):
    return parts_version_text()

def is_parts_version_beta():
    if _PARTS_VERSION[-4:].lower()=='beta':
        return True
    return False

def is_parts_version_beta_env(env):
    return is_parts_version_beta()

def PartsExtensionVersion():
    import version
    if is_parts_version_beta():
        return version.version(_PARTS_VERSION[:-5])
    return version.version(_PARTS_VERSION)

def PartsExtensionVersion_env(env):
    return PartsExtensionVersion()


# add to parts file as globals
common.add_parts_object('PartVersionString',parts_version_text)
common.add_parts_object('IsPartsExtensionVersionBeta',is_parts_version_beta)
common.add_parts_object('PartsExtensionVersion',PartsExtensionVersion)

#add to Sconsctruct as globals
common.add_global_value('PartVersionString',parts_version_text_env)
common.add_global_value('IsPartsExtensionVersionBeta',is_parts_version_beta_env)
common.add_global_value('PartsExtensionVersion',PartsExtensionVersion_env)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.PartVersionString=parts_version_text_env
SConsEnvironment.IsPartsExtensionVersionBeta=is_parts_version_beta_env
SConsEnvironment.PartsExtensionVersion=PartsExtensionVersion_env