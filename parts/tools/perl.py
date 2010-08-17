
import GnuCommon.perl
import parts.reporter as reporter

def generate(env):
    """Add Builders and construction variables for gcc to an Environment."""
    # no builder yets.. add a PerlCommand()?
    
    # set up shell env for running compiler
    GnuCommon.perl.perl.MergeShellEnv(env)
    #reporter.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('perl',env['PERL']['VERSION'],env['TARGET_PLATFORM']))

def exists(env):
    return GnuCommon.perl.perl.Exists(env)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
