from common import gxx, GnuInfo
from parts.tools.Common.Finders import PathFinder,ScriptFinder
from parts.platform_info import system_config

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[system_config('posix','x86'),system_config('posix','x86_64')],
    targets=[system_config('posix','x86'),system_config('posix','x86_64')],
    info=[
    GnuInfo(
        #standard location, however there might be
        # some posix offshoot that might tweak this directory
        # so we allow this to be set
        install_scanner=[
            PathFinder(['/usr/bin'])
            ],
        opt_dirs=[
                '/opt/'
            ],
        script=None,
        subst_vars={},
        shell_vars={'PATH':'${GXX.INSTALL_ROOT}'},
        test_file='g++'
        )
    ]
)

gxx.Register(
    # we assume that the system has teh correct libraies installed to do a cross build
    # or that the user add theh extra check for the stuff the need
    hosts=[system_config('cygwin','x86'),system_config('cygwin','x86_64')],
    targets=[system_config('cygwin','x86'),system_config('cygwin','x86_64')],
    info=[
    GnuInfo(
        #standard location, however there might be
        # some posix offshoot that might tweak this directory
        # so we allow this to be set
        install_scanner=[
            PathFinder(['/usr/bin'])
            ],
        opt_dirs=[
                '/opt/'
            ],
        script=None,
        subst_vars={},
        shell_vars={'PATH':'${GXX.INSTALL_ROOT}'},
        test_file='g++'
        )
    ]
)

gxx.Register(
    # we assume that the system has teh correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[system_config('cygwin','ia64')],
    targets=[system_config('cygwin','ia64')],
    info=[
    GnuInfo(
        #standard location, however there might be
        # some posix offshoot that might tweak this directory
        # so we allow this to be set
        install_scanner=[
            PathFinder(['/usr/bin'])
            ],
        opt_dirs=[
                '/opt/'
            ],
        script=None,
        subst_vars={},
        shell_vars={'PATH':'${GXX.INSTALL_ROOT}'},
        test_file='g++'
        )
    ]
)

# add other combo later (sun, Mac, etc...)





