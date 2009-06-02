
import IntelCommon
import SCons.Util
import SCons.Warnings
import os



def generate(env):
    
    is_windows=env['TARGET_SYSTEM'].Platform=='win32'
    if is_windows:
        env['CC']        = 'icl'
        env['CXX']       = 'icl'
        env['LINK']      = 'xilink'
    else:
        env['CC']        = 'icc'
        env['CXX']       = 'icpc'
        # Don't reset LINK here;
        # use smart_link which should already be here from link.py.
        #env['LINK']      = '$CC'
        env['AR']        = 'xiar'
        env['LD']        = 'xild' # not used by default

    
    if is_windows:
        # Look for license file dir
        # in system environment, and default location.
        envlicdir = os.environ.get("INTEL_LICENSE_FILE", '')
        defaultlicdir = r'C:\Program Files\Common Files\Intel\Licenses'

        licdir = None
        for ld in [envlicdir]:
            if ld and os.path.exists(ld):
                licdir = ld
                break
        if licdir is None:
            licdir = defaultlicdir
            if not os.path.exists(licdir):
                class ICLLicenseDirWarning(SCons.Warnings.Warning):
                    pass
                SCons.Warnings.enableWarningClass(ICLLicenseDirWarning)
                SCons.Warnings.warn(ICLLicenseDirWarning,
                                    "Intel license dir was not found."
                                    "  Tried using the INTEL_LICENSE_FILE environment variable (%s) and the default path (%s)."
                                    "  Using the default path as a last resort."
                                        % (envlicdir, defaultlicdir))
        env['ENV']['INTEL_LICENSE_FILE'] = licdir
        
    IntelCommon.Intelc.MergeShellEnv(env)

def exists(env):
    return IntelCommon.Intelc.Exists(env)

# end of file
