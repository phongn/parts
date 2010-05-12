from common import msvc,framework_root,framework_root64
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder,EnvFinder,PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform
import parts.reporter as reporter
import os
import SCons.Platform

def get_current_sdk():
    '''Get SDK path based on reg key used for vc 10.0'''

    try:
        return get_current_sdk.cache
    except AttributeError:
        r=RegFinder([
                r'SOFTWARE\Wow6432Node\Microsoft\Microsoft SDKs\Windows\v7.0A\InstallationFolder',
                r'SOFTWARE\Microsoft\Microsoft SDKs\Windows\v7.0A\InstallationFolder'
                    ])
        dir=r()
        if dir is None:
            dir=''
        get_current_sdk.cache=dir
        return get_current_sdk.cache

## version 10 .. 2010
# 32-bit
msvc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','x86')],
    info=[
        ToolInfo(
            version='10.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\10.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS100COMNTOOLS'
                ],'../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC',
                    r'C:\Program Files\Microsoft Visual Studio 10.0\VC'
                ])
            ],
            script=ScriptFinder('${CL.VSINSTALL}/Common7/Tools/vcvars32.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}/..',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64(),
            'WINSDK_ROOT':get_current_sdk()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/VC/VCPackages'+os.pathsep+
                            '${MSVC.VCINSTALL}/HTML Help Workshop'+os.pathsep+
                            '${MSVC.VCINSTALL}/Team Tools/Performance Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin/NETFX4.0 Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin'
                            ,
                            
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/include'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib'+os.pathsep
                        ,
                        'LIBPATH':
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/LIB'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        },
            test_file='cl.exe'
            )
        ]
    )

# 64-bit native
msvc.Register(
    hosts=[SystemPlatform('win32','x86_64')],
    targets=[SystemPlatform('win32','x86_64')],
    info=[
        ToolInfo(
            version='10.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\10.0\Setup\VC\ProductDir',
                ]),
                EnvFinder([
                    'VS100COMNTOOLS'
                ],'../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/AMD64/vcvars64.bat.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}/..',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64(),
            'WINSDK_ROOT':get_current_sdk()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin/AMD64'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/VC/VCPackages'+os.pathsep+
                            '${MSVC.VCINSTALL}/HTML Help Workshop'+os.pathsep+
                            '${MSVC.VCINSTALL}/Team Tools/Performance Tools/x64'+os.pathsep+
                            '${MSVC.VCINSTALL}/Team Tools/Performance Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin/NETFX4.0 Tools/x64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin/x64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin'
                            ,
                            
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/include'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/AMD64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/x64'+os.pathsep
                        ,
                        'LIBPATH':
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/AMD64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/x64'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        },
            test_file='cl.exe'
            )
        ]
    )

#cross - 64-bit. This also works for ia64
msvc.Register(
    hosts=[SystemPlatform('win32','any')],# say 'any' as the code will preffer this less than a native version
    targets=[SystemPlatform('win32','x86_64')],
    info=[
        ToolInfo(
            version='10.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\10.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS100COMNTOOLS'
                ],'../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC'
                    r'C:\Program Files\Microsoft Visual Studio 10.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/x86_amd64/vcvarsx86_amd64.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}/..',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64(),
            'WINSDK_ROOT':get_current_sdk()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin/x86_amd64'+os.pathsep+
                            '${MSVC.VCINSTALL}/bin/'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/VC/VCPackages'+os.pathsep+
                            '${MSVC.VCINSTALL}/HTML Help Workshop'+os.pathsep+
                            '${MSVC.VCINSTALL}/Team Tools/Performance Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin/NETFX4.0 Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin'
                            ,
                            
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/include'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/AMD64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/x64'+os.pathsep
                        ,
                        'LIBPATH':
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/AMD64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/AMD64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/x64'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        },
            test_file='x86_amd64/cl.exe'
            )
        ]
    )  

# ia64 native 
# not fully test as we lack a machine
msvc.Register(
    hosts=[SystemPlatform('win32','ia64')],
    targets=[SystemPlatform('win32','ia64')],
    info=[
        ToolInfo(
            version='10.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\10.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS100COMNTOOLS'
                ],'../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC'
                    r'C:\Program Files\Microsoft Visual Studio 10.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/x86_ia64/vcvars_ia64.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}/..',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64(),
            'WINSDK_ROOT':get_current_sdk()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin/ia64'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/VC/VCPackages'+os.pathsep+
                            '${MSVC.VCINSTALL}/HTML Help Workshop'+os.pathsep+
                            '${MSVC.VCINSTALL}/Team Tools/Performance Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin/NETFX4.0 Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin'
                            ,
                            
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/include'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/ia64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/ia64'+os.pathsep
                        ,
                        'LIBPATH':
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/ia64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/ia64'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        },
            test_file='x86_ia64/cl.exe'
            )
        ]
    )    

# ia64 cross 
msvc.Register(
    hosts=[SystemPlatform('win32','any')],
    targets=[SystemPlatform('win32','ia64')],
    info=[
        ToolInfo(
            version='10.0',
            install_scanner=[
                RegFinder([
                    r'Software\Wow6432Node\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VisualStudio\10.0\Setup\VC\ProductDir',
                    r'Software\Wow6432Node\Microsoft\VCExpress\10.0\Setup\VC\ProductDir',
                    r'Software\Microsoft\VCExpress\10.0\Setup\VC\ProductDir'
                ]),
                EnvFinder([
                    'VS100COMNTOOLS'
                ],'../../VC'),
                PathFinder([
                    r'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC'
                    r'C:\Program Files\Microsoft Visual Studio 10.0\VC'
                ])
            ],
            script=ScriptFinder('${MSVC.VCINSTALL}/bin/x86_ia64/vcvarsx86_ia64.bat'),
            subst_vars={
            'VCINSTALL':'${MSVC.INSTALL_ROOT}',
            'VSINSTALL':'${MSVC.INSTALL_ROOT}/..',
            'FRAMEWORK_ROOT':framework_root(),
            'FRAMEWORK_ROOT64':framework_root64(),
            'WINSDK_ROOT':get_current_sdk()
            },
            shell_vars={
                        'PATH':
                            '${MSVC.VCINSTALL}/bin/x86_ia64'+os.pathsep+
                            '${MSVC.VCINSTALL}/bin/'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/IDE'+os.pathsep+
                            '${MSVC.VSINSTALL}/Common7/Tools'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/VC/VCPackages'+os.pathsep+
                            '${MSVC.VCINSTALL}/HTML Help Workshop'+os.pathsep+
                            '${MSVC.VCINSTALL}/Team Tools/Performance Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin/NETFX4.0 Tools'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/bin'
                            ,
                            
                        'INCLUDE':
                            '${MSVC.VCINSTALL}/INCLUDE'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/INCLUDE'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/include'
                        ,
                        'LIB':
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/ia64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/ia64'+os.pathsep
                        ,
                        'LIBPATH':
                            '${MSVC.FRAMEWORK_ROOT64}/v4.0.30319'+os.pathsep+
                            '${MSVC.FRAMEWORK_ROOT64}/v3.5'+os.pathsep+
                            '${MSVC.VCINSTALL}/ATLMFC/LIB/ia64'+os.pathsep+
                            '${MSVC.VCINSTALL}/LIB/ia64'+os.pathsep+
                            '${MSVC.WINSDK_ROOT}/lib/ia64'
                        ,
                        'SYSTEMROOT':SCons.Platform.win32.get_system_root()
                        },
            test_file='x86_ia64/cl.exe'
            )
        ]
    )    


    
    
    
    