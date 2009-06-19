
import GnuCommon.perl

def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    # no builder yets.. add a PerlCommand()?
    
    # set up shell env for running compiler
    GnuCommon.perl.MergeShellEnv(env)

def exists(env):
    return GnuCommon.perl.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
