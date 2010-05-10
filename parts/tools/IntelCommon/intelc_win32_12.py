from common import Intelc
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder,EnvFinder,PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform
import os

#12.0 is in beta currently.. values may change

# 32-bit 12.0 
Intelc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','x86')],
    info=[
        ToolInfo(
            version='12.0',
            install_scanner=[
                EnvFinder([
                    'ICPP_COMPILER12'
                ]),
                PathFinder([
                    r'C:\Program Files (x86)\Intel\Parallel Studio 2011\Composer'
                    r'C:\Program Files\Intel\Parallel Studio 2011\Composer'
                ])
            ],
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat','ia32'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include'+os.pathsep+
                        '${INTELC.INSTALL_ROOT}/compiler/include/ia32'
                        ,
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/ia32'
                        },
            test_file='icl.exe'
            )
        ]
    )


# 64-bit 12.0 cross 
Intelc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','x86_64')],
    info=[
        ToolInfo(
            version='12.0',
            install_scanner=[
                EnvFinder([
                    'ICPP_COMPILER12'
                ]),
                PathFinder([
                    r'C:\Program Files (x86)\Intel\Parallel Studio 2011\Composer'
                    r'C:\Program Files\Intel\Parallel Studio 2011\Composer'
                ])
            ],
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat','ia32_intel64'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32_intel64',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/compiler/include'+os.pathsep+
                        '${INTELC.INSTALL_ROOT}/compiler/include/ia32_intel64'
                        ,
                        'LIB':'${INTELC.INSTALL_ROOT}/compiler/lib/ia32_intel64'
                        },
            test_file='icl.exe'
            )
        ]
    )




