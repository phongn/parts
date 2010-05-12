from common import Intelc,IntelcInfo
import common
import filescanner
from parts.tools.Common.Finders import RegFinder,EnvFinder,PathFinder,ScriptFinder
from parts.platform_info import SystemPlatform
import os



# 32-bit 11.1 
Intelc.Register(
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('posix','x86')],
    info=[
        IntelcInfo(
            version='11.*',
            install_scanner=filescanner.file_scanner11(
                '/opt/intel/Compiler',
                common.intel_11_outer,
                common.intel_11_inner,
                'ia32',
                'ICPP_COMPILER11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ia32/iclvars_ia32.bat'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia32/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/ia32/'                      
                        },
            test_file='icc'
            )
        ]
    )   
    
# 64-bit 11.1
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64')],
    targets=[SystemPlatform('posix','x86_64')],
    info=[
        IntelcInfo(
            version='11.*',
                        install_scanner=filescanner.file_scanner11(
                '/opt/intel/Compiler',
                common.intel_11_outer,
                common.intel_11_inner,
                'EM64T',
                'ICPP_COMPILER11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/IA32_Intel64/intel64.sh'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/intel64/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/intel64'                     
                        },
            test_file='icc'
            )
        ]
    ) 


    
# 64-bit ia64 11.x
Intelc.Register(
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('posix','ia64')],
    info=[
        IntelcInfo(
            version='11.*',
            install_scanner=filescanner.file_scanner11(
                '/opt/intel/Compiler',
                common.intel_11_outer,
                common.intel_11_inner,
                'ia64',
                'ICPP_COMPILER11'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.sh'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/ia64',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/ia64'
                        },
            test_file='icc'
            )
        ]
    ) 

# 32-bit 10.x
Intelc.Register(
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('posix','x86')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=filescanner.file_scanner9_10(
                '/opt/intel/cc',
                common.intel_10_posix,
                'ia32',
                'ICPP_COMPILER10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                        },
            test_file='icc'
            )
        ]
    )   
    
# 64-bit 10.x
Intelc.Register(
    hosts=[SystemPlatform('posix','x86_64')],
    targets=[SystemPlatform('posix','x86_64')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=filescanner.file_scanner9_10(
                '/opt/intel/cce',
                common.intel_10_posix,
                'EM64T',
                'ICPP_COMPILER10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                        },
            test_file='icc'
            )
        ]
    ) 
    
# 64-bit ia64 10.x
Intelc.Register(
    hosts=[SystemPlatform('posix','any')],
    targets=[SystemPlatform('posix','ia64')],
    info=[
        IntelcInfo(
            version='10.*',
            install_scanner=filescanner.file_scanner9_10(
                '/opt/intel/cc',
                common.intel_10_posix,
                'ia64',
                'ICPP_COMPILER10'),
            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.sh'),
            subst_vars={
            
            },
            shell_vars={
                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                        },
            test_file='icc'
            )
        ]
    ) 

# 9.x 64-bit    
Intelc.Register(
     hosts=[SystemPlatform('posix','x86_64')],
     targets=[SystemPlatform('posix','x86_64')],
     info=[
         IntelcInfo(
             version='9.*',
             install_scanner=filescanner.file_scanner9_10(
                 '/opt/intel/cce',
                 common.intel_9_posix,
                 'EM64T',
                 'ICPP_COMPILER9'),
             script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
             subst_vars={
             
             },
             shell_vars={
                         'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                         'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                         'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                         },
             test_file='icc'
             )
         ]
     ) 

#9.x 32-bit
Intelc.Register(
     hosts=[SystemPlatform('posix','any')],
     targets=[SystemPlatform('posix','x86')],
     info=[
         IntelcInfo(
             version='9.*',
             install_scanner=filescanner.file_scanner9_10(
                 '/opt/intel/cc',
                 common.intel_9_posix,
                 'ia32',
                 'ICPP_COMPILER9'),
             script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/iccvars.csh'),
             subst_vars={
             
             },
             shell_vars={
                         'PATH':'${INTELC.INSTALL_ROOT}/bin/',
                         'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
                         'LIB':'${INTELC.INSTALL_ROOT}/lib/'
                         },
             test_file='icc'
             )
         ]
     ) 
  

