from common import Intelc,IntelcInfo
import common
import filescanner
from parts.tools.Common.Finders import RegFinder,EnvFinder,PathFinder,ScriptFinder
from parts.platform_info import system_config
import os



# 32-bit 11.1 
Intelc.Register(
    hosts=[system_config('posix','any')],
    targets=[system_config('posix','x86')],
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
    hosts=[system_config('posix','x86_64')],
    targets=[system_config('posix','x86_64')],
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


    
# 64-bit ia64 11.x todo
#Intelc.Register(
#    hosts=[system_config('posix','any')],
#    targets=[system_config('posix','ia64')],
#    info=[
#        IntelcInfo(
#            version='11.*',
#            install_scanner=filescanner.file_scanner11(
#                '/opt/intel/Compiler/11.0',
#                common.intel_11_outer,
#                common.intel_11_inner,
#                'ia32',
#                'ICPP_COMPILER11),
#            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
#            subst_vars={
#            
#            },
#            shell_vars={
#                        'PATH':'${INTELC.INSTALL_ROOT}/bin/Itanium',
#                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
#                        'LIB':'${INTELC.INSTALL_ROOT}/lib/Itanium'
#                        },
#            test_file='icl.exe'
#            )
#        ]
#    ) 

# 32-bit 10.x
Intelc.Register(
    hosts=[system_config('posix','any')],
    targets=[system_config('posix','x86')],
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
    hosts=[system_config('posix','x86_64')],
    targets=[system_config('posix','x86_64')],
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
#Intelc.Register(
#    hosts=[system_config('posix','any')],
#    targets=[system_config('posix','ia64')],
#    info=[
#        IntelcInfo(
#            version='10.*',
#            install_scanner=filescanner.file_scanner9_10(
#                '/opt/intel/cc',
#                common.intel_10_posix,
#                'ia32',
#                'ICPP_COMPILER10'),
#            script=ScriptFinder('${INTELC.INSTALL_ROOT}/bin/ICLVars.bat'),
#            subst_vars={
#            
#            },
#            shell_vars={
#                        'PATH':'${INTELC.INSTALL_ROOT}/bin/',
#                        'INCLUDE':'${INTELC.INSTALL_ROOT}/include/',
#                        'LIB':'${INTELC.INSTALL_ROOT}/lib/'
#                        },
#            test_file='icl.exe'
#            )
#        ]
#    ) 
    
    
