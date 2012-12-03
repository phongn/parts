import os
from common import gxx, GnuInfo
from parts.tools.Common.Finders import PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform
from parts.tools.Common.ToolInfo import ToolInfo
import android

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
        test_file='g++',
        opt_pattern='gcc\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )
    ]
)

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix','ia64')],
    targets=[SystemPlatform('posix','ia64')],
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
        test_file='g++',
        opt_pattern='gcc\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )
    ]
)

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
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
        test_file='g++',
        opt_pattern='gcc\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )
    ]
)

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
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
        test_file='g++',
        opt_pattern='gcc\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )
    ]
)

# add other combo later (sun, Mac, etc...)

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('sunos','any')],
    targets=[SystemPlatform('sunos','any')],
    info=[
    GnuInfo(
        #standard location, however there might be
        # some posix offshoot that might tweak this directory
        # so we allow this to be set
        install_scanner=[
            PathFinder(['/usr/sfw/bin'])
            ],
        opt_dirs=[
                '/opt/'
            ],
        script=None,
        subst_vars={},
        shell_vars={'PATH':'${GXX.INSTALL_ROOT}'},
        test_file='g++',
        opt_pattern='gcc\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )
    ]
)

#mac
gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('darwin','any')],
    targets=[SystemPlatform('darwin','any')],
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
        test_file='g++',
        opt_pattern='gcc\-?([0-9]+\.[0-9]+\.[0-9]*|[0-9]+\.[0-9]+|[0-9]+)'
        )

    ]
)

# android
#pre r8
gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('android','x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"],'x86','i686-android-linux-','g++.exe'),            
            script=None,
            subst_vars={
                        'SYS_ROOT':r'"${GXX.INSTALL_ROOT}\platforms\android-14\arch-x86"',
                        'LIBRARY_PATH':'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\libs\x86'
                        },
            shell_vars={
                        'PATH':r'${GXX.INSTALL_ROOT}\toolchains\x86-${GXX.VERSION}\prebuilt\windows\bin',
                        'CPLUS_INCLUDE_PATH':r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\include\backward'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\libs\x86\include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\toolchains\x86-${GXX.VERSION}\prebuilt\windows\include', 
                        'LIBRARY_PATH':'${GXX.LIBRARY_PATH}'
                        },
            test_file='i686-android-linux-g++.exe'
            )
    ]
)
#post r8
gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('android','x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"],'x86','i686-linux-android-','g++.exe'),            
            script=None,
            subst_vars={
                        'SYS_ROOT':r'"${GXX.INSTALL_ROOT}\platforms\android-14\arch-x86"',
                        'LIBRARY_PATH':'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\${GXX.VERSION}\libs\x86'
                        },
            shell_vars={
                        'PATH':r'${GXX.INSTALL_ROOT}\toolchains\x86-${GXX.VERSION}\prebuilt\windows\bin',
                        'CPLUS_INCLUDE_PATH':r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\${GXX.VERSION}\include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\${GXX.VERSION}\include\backward'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\${GXX.VERSION}\libs\x86\include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\toolchains\x86-${GXX.VERSION}\prebuilt\windows\include', 
                        'LIBRARY_PATH':'${GXX.LIBRARY_PATH}'
                        },
            test_file='i686-linux-android-g++.exe'
            )
    ]
)


gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('android','arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.win_scanner(["NDK_ROOT"],'arm','arm-linux-androideabi-','g++.exe'),        
            script=None,
            subst_vars={
                        'SYS_ROOT':r'"${GXX.INSTALL_ROOT}\platforms\android-14\arch-arm"',
                        'LIBRARY_PATH':'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\libs\armeabi-v7a'                                                    
                        },
            shell_vars={
                        'PATH':r'${GXX.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${GXX.VERSION}\prebuilt\windows\bin',
                        'CPLUS_INCLUDE_PATH':r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\include\backward'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\sources\cxx-stl\gnu-libstdc++\libs\armeabi\include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}\toolchains\arm-linux-androideabi-${GXX.VERSION}\prebuilt\windows\include',
                        'LIBRARY_PATH':'${GXX.LIBRARY_PATH}'
                        },
            test_file='arm-linux-androideabi-g++.exe'
            )
    ]
)
#pre r8
gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('android','x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"],'x86','i686-android-linux-','g++'),  
            script=None,
            subst_vars={
                        'SYS_ROOT':r'"${GXX.INSTALL_ROOT}/platforms/android-14/arch-x86"',
                        'LIBRARY_PATH':'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/x86'
                        },
            shell_vars={
                        'PATH':r'${GXX.INSTALL_ROOT}/toolchains/x86-${GXX.VERSION}/prebuilt/linux-x86/bin',
                        'CPLUS_INCLUDE_PATH':r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include/backward'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/x86/include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/toolchains/x86-${GXX.VERSION}/prebuilt/linux-x86/include',
                        'LIBRARY_PATH':'${GXX.LIBRARY_PATH}'
                                                    
                        },
            test_file='i686-android-linux-g++'
            )
    ]
)
#post r8
gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('android','x86')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"],'x86','i686-linux-android-','g++'),  
            script=None,
            subst_vars={
                        'SYS_ROOT':r'"${GXX.INSTALL_ROOT}/platforms/android-14/arch-x86"',
                        'LIBRARY_PATH':'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/x86'
                        },
            shell_vars={
                        'PATH':r'${GXX.INSTALL_ROOT}/toolchains/x86-${GXX.VERSION}/prebuilt/linux-x86/bin',
                        'CPLUS_INCLUDE_PATH':r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/include/backward'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/${GXX.VERSION}/libs/x86/include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/toolchains/x86-${GXX.VERSION}/prebuilt/linux-x86/include',
                        'LIBRARY_PATH':'${GXX.LIBRARY_PATH}'
                                                    
                        },
            test_file='i686-linux-android-g++'
            )
    ]
)

gxx.Register(
    # we assume that the system has the correct libraies installed to do a cross build
    # or that the user add the extra check for the stuff the need
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('android','arm')],
    info=[
        ToolInfo(
            version='*',
            install_scanner=android.posix_scanner(["NDK_ROOT"],'arm','arm-linux-androideabi-','g++'),    
            script=None,
            subst_vars={
                        'SYS_ROOT':r'"${GXX.INSTALL_ROOT}/platforms/android-14/arch-arm"',
                        'LIBRARY_PATH':'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/armeabi-v7a'
                        },
            shell_vars={
                        'PATH':r'${GXX.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GXX.VERSION}/prebuilt/linux-x86/bin',
                        'CPLUS_INCLUDE_PATH':r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/include/backward'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/sources/cxx-stl/gnu-libstdc++/libs/armeabi-v7a/include'+os.pathsep+
                            r'${GXX.INSTALL_ROOT}/toolchains/arm-linux-androideabi-${GXX.VERSION}/prebuilt/linux-x86/include',
                        'LIBRARY_PATH':'${GXX.LIBRARY_PATH}'
                                                    
                        },
            test_file='arm-linux-androideabi-g++'
            )
    ]
)


