
from setup import setup_env
from query import msvc_exists
from common import is_win64


def validate_vars(env):
    """Validate the PCH and PCHSTOP construction variables."""
    if env.has_key('PCH') and env['PCH']:
        if not env.has_key('PCHSTOP'):
            raise SCons.Errors.UserError, "The PCHSTOP construction must be defined if PCH is defined."
        if not SCons.Util.is_String(env['PCHSTOP']):
            raise SCons.Errors.UserError, "The PCHSTOP construction variable must be a string: %r"%env['PCHSTOP']



