import os.path
import os
import SCons.Util

import MSCommon.vsx_sdk
from MSCommon import vssdk


ctc_action = SCons.Action.Action('$CTC_COM', '$CTC_COMSTR')
ctc_builder = SCons.Builder.Builder(action=ctc_action,
                                    src_suffix='.ctc',
                                    suffix='.cto',
                                    src_builder=[],
                                    source_scanner=SCons.Tool.SourceFileScanner)
SCons.Tool.SourceFileScanner.add_scanner('.ctc', SCons.Defaults.CScan)


def generate(env):#, version=None, abi=None, topdir=None, verbose=0):
   
    env['INCPREFIX']  = '/I'
    env['INCSUFFIX']  = ''
    env['_CTC_INCFLAGS'] = '$( ${_concat(INCPREFIX, CTC_INCLUDES, INCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['CTC']='ctc'
    env['CTC_INCLUDES']=SCons.Util.CLVar([])#['${VSSDK.INSTALL_ROOT}\\VisualStudioIntegration\\Common\\Inc','${VSSDK.INSTALL_ROOT}\\VisualStudioIntegration\\Common\\Inc\\office10']
    env['CTC_FLAGS']=SCons.Util.CLVar(['-nologo','-Ccl'])
    env['CTC_COM'] = '$CTC $SOURCE $TARGET $CTC_FLAGS $_CTC_INCFLAGS'
    env['BUILDERS']['CTC'] = ctc_builder
        
    vssdk.MergeShellEnv(env)



def exists (env):
    return vssdk.Exists(env)