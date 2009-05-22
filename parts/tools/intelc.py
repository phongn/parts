


def generate(env):
    

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
        # in system environment, registry, and default location.
        envlicdir = os.environ.get("INTEL_LICENSE_FILE", '')
        K = ('SOFTWARE\Intel\Licenses')
        try:
            k = SCons.Util.RegOpenKeyEx(SCons.Util.HKEY_LOCAL_MACHINE, K)
            reglicdir = SCons.Util.RegQueryValueEx(k, "w_cpp")[0]
        except (AttributeError, SCons.Util.RegError):
            reglicdir = ""
        defaultlicdir = r'C:\Program Files\Common Files\Intel\Licenses'

        licdir = None
        for ld in [envlicdir, reglicdir]:
            if ld and os.path.exists(ld):
                licdir = ld
                break
        if not licdir:
            licdir = defaultlicdir
            if not os.path.exists(licdir):
                class ICLLicenseDirWarning(SCons.Warnings.Warning):
                    pass
                SCons.Warnings.enableWarningClass(ICLLicenseDirWarning)
                SCons.Warnings.warn(ICLLicenseDirWarning,
                                    "Intel license dir was not found."
                                    "  Tried using the INTEL_LICENSE_FILE environment variable (%s), the registry (%s) and the default path (%s)."
                                    "  Using the default path as a last resort."
                                        % (envlicdir, reglicdir, defaultlicdir))
        env['ENV']['INTEL_LICENSE_FILE'] = licdir

def exists(env):
    if not (is_linux or is_windows):
        # can't handle this platform
        return 0

    try:
        versions = get_all_compiler_versions()
    except (SCons.Util.RegError, IntelCError):
        versions = None
    detected = versions is not None and len(versions) > 0
    if not detected:
        # try env.Detect, maybe that will work
        if is_windows:
            return env.Detect('icl')
        elif is_linux:
            return env.Detect('icc')
    return detected

# end of file
