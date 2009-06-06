from common import gxx, GnuInfo
from parts.tools.Common.Finders import PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix','x86'),SystemPlatform('posix','x86_64')],
    targets=[SystemPlatform('posix','x86'),SystemPlatform('posix','x86_64')],
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
    hosts=[SystemPlatform('cygwin','x86'),SystemPlatform('cygwin','x86_64')],
    targets=[SystemPlatform('cygwin','x86'),SystemPlatform('cygwin','x86_64')],
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
    hosts=[SystemPlatform('cygwin','ia64')],
    targets=[SystemPlatform('cygwin','ia64')],
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





