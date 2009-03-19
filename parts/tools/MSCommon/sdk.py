#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

__doc__ = """Module to detect the Platform/Windows SDK

PSDK 2003 R1 is the earliest version detected.
"""

import os

import SCons.Errors
from common import debug, read_reg
import part_compat
import SCons.Util

# SDK Checks. This is of course a mess as everything else on MS platforms. Here
# is what we do to detect the SDK:
#
# For Windows SDK >= 6.0: just look into the registry entries:
#   HKLM\Software\Microsoft\Microsoft SDKs\Windows
# All the keys in there are the available versions.
#
# For Platform SDK before 6.0 (2003 server R1 and R2, etc...), there does not
# seem to be any sane registry key, so the precise location is hardcoded.
#
# For versions below 2003R1, it seems the PSDK is included with Visual Studio?
#
# Also, per the following:
#     http://benjamin.smedbergs.us/blog/tag/atl/
# VC++ Professional comes with the SDK, VC++ Express does not.

# Location of the SDK (checked for 6.1 only)
_CURINSTALLED_SDK_HKEY_ROOT = \
        r"Software\Microsoft\Microsoft SDKs\Windows\CurrentInstallFolder"


class SDKDefinition:
    """
    An abstract base class for trying to find installed SDK directories.
    """
    def __init__(self, version, **kw):
        self.version = version
        self.__dict__.update(kw)

    def find_sdk_dir(self):
        """Try to find the MS SDK from the registry.

        Return None if failed or the directory does not exist.
        """
        if not SCons.Util.can_read_reg:
            debug('find_sdk_dir():  can not read registry')
            return None

        hkey = self.HKEY_FMT % self.hkey_data

        try:
            sdk_dir = read_reg(hkey)
        except WindowsError, e:
            debug('find_sdk_dir(): no registry key %s' % hkey)
            return None

        if not os.path.exists(sdk_dir):
            debug('find_sdk_dir():  %s not on file system' % sdk_dir)
            return None

        ftc = os.path.join(sdk_dir, self.sanity_check_file)
        if not os.path.exists(ftc):
            debug("find_sdk_dir():  sanity check %s not found" % ftc)
            return None

        return sdk_dir

    def get_sdk_dir(self):
        """Return the MSSSDK given the version string."""
        try:
            return self._sdk_dir
        except AttributeError:
            sdk_dir = self.find_sdk_dir()
            self._sdk_dir = sdk_dir
            return sdk_dir
    
        

class WindowsSDK(SDKDefinition):
    """
    A subclass for trying to find installed Windows SDK directories.
    """
    HKEY_FMT = r'Software\Microsoft\Microsoft SDKs\Windows\v%s\InstallationFolder'
    def __init__(self, *args, **kw):
        apply(SDKDefinition.__init__, (self,)+args, kw)
        self.hkey_data = self.version
        self.has_atlmfc=False

class PlatformSDK(SDKDefinition):
    """
    A subclass for trying to find installed Platform SDK directories.
    """
    HKEY_FMT = r'Software\Microsoft\MicrosoftSDK\InstalledSDKS\%s\Install Dir'
    def __init__(self, *args, **kw):
        apply(SDKDefinition.__init__, (self,)+args, kw)
        self.hkey_data = self.uuid
        self.has_atlmfc=True
   
    
# The list of support SDKs which we know how to detect.
#
# The first SDK found in the list is the one used by default if there
# are multiple SDKs installed.  Barring good reasons to the contrary,
# this means we should list SDKs with from most recent to oldest.
#
# If you update this list, update the documentation in Tool/mssdk.xml.
SupportedSDKList = [
    WindowsSDK('6.1',
                sanity_check_file=r'bin\SetEnv.Cmd'),
                

    WindowsSDK('6.0A',
               sanity_check_file=r'include\windows.h'),

    WindowsSDK('6.0',
               sanity_check_file=r'bin\gacutil.exe'),

    PlatformSDK('2003R2',
                sanity_check_file=r'SetEnv.Cmd',
                uuid="D2FF9F89-8AA2-4373-8A31-C838BF4DBBE1",
                ),

    PlatformSDK('2003R1',
                sanity_check_file=r'SetEnv.Cmd',
                uuid="8F9E5EF3-A9A5-491B-A889-C58EFFECE8B3",
                ),
]

SupportedSDKMap = {}
for sdk in SupportedSDKList:
    SupportedSDKMap[sdk.version] = sdk


# Finding installed SDKs isn't cheap, because it goes not only to the
# registry but also to the disk to sanity-check that there is, in fact,
# an SDK installed there and that the registry entry isn't just stale.
# Find this information once, when requested, and cache it.

InstalledSDKList = None
InstalledSDKMap = None

def get_installed_sdks():
    global InstalledSDKList
    global InstalledSDKMap
    if InstalledSDKList is None:
        InstalledSDKList = []
        InstalledSDKMap = {}
        for sdk in SupportedSDKList:
            debug('trying to find SDK %s' % sdk.version)
            if sdk.get_sdk_dir():
                debug('found SDK %s' % sdk.version)
                InstalledSDKList.append(sdk)
                InstalledSDKMap[sdk.version] = sdk
    return InstalledSDKList


# We may be asked to update multiple construction environments with
# SDK information.  When doing this, we check on-disk for whether
# the SDK has 'mfc' and 'atl' subdirectories.  Since going to disk
# is expensive, cache results by directory.

SDKEnvironmentUpdates = {'x86':{},'x86_64':{},'ia64':{}}

def set_sdk_by_directory(env, sdk_dir,use_mfc=True):
    global SDKEnvironmentUpdates
    arch=env['TARGET_PLATFORM'].Architecture()
    try:
        env_tuple_list = SDKEnvironmentUpdates[arch][sdk_dir]
    except KeyError:
        env_tuple_list = []
        SDKEnvironmentUpdates[arch][sdk_dir] = env_tuple_list
        include_path = os.path.join(sdk_dir, 'include') 
        # test MFC ATL
        # Only for older Platform SDK
        if use_mfc:
            mfc_path = os.path.join(include_path, 'mfc')
            atl_path = os.path.join(include_path, 'atl')
            mfc_lib=''
            if arch=='x86_64':
                mfc_lib=os.path.join(sdk_dir,'lib\\AMD64\\atlmfc')
            elif arch=='ia64':
                mfc_lib=os.path.join(sdk_dir,'lib\\ia64\\mfc')
            # double check...
            if os.path.exists(mfc_path):
                env_tuple_list.append(('INCLUDE', mfc_path))
            if os.path.exists(atl_path):
                env_tuple_list.append(('INCLUDE', atl_path))
            if os.path.exists(mfc_lib):
                env_tuple_list.append(('LIB', mfc_lib))
                env_tuple_list.append(('LIBPATH', mfc_lib))
            
        ## setup the include path
        env_tuple_list.append(('INCLUDE', include_path))
        
        ## setup lib path
        if arch=='x86_64':
            lib_tmp=os.path.join(sdk_dir,'lib\\AMD64')
            if os.path.exists(lib_tmp)==False:
                lib_tmp=os.path.join(sdk_dir,'lib\\x64')
        elif arch=='ia64':
            lib_tmp=os.path.join(sdk_dir,'lib\\IA64')                
        else:
            lib_tmp=os.path.join(sdk_dir,'lib')
        env_tuple_list.append(('LIB', lib_tmp))
        env_tuple_list.append(('LIBPATH', lib_tmp))
        
        ##setup path
        bin_tmp=''
        if arch=='x86_64':
            #assume older cases first
            bin_tmp=os.path.join(sdk_dir,'bin\\win64\\x86\\AMD64')
            if os.path.exists(bin_tmp)==False:
                # This is a newer SDK, or some failure happened
                bin_tmp=''
        elif arch=='ia64':
            #assume older cases first
            bin_tmp=os.path.join(sdk_dir,'bin\\win64\\')
            if os.path.exists(bin_tmp)==False:
                # This is a newer SDK, or some failure happened
                bin_tmp=''
        if bin_tmp != '':
            env_tuple_list.append(('PATH', bin_tmp))
        env_tuple_list.append(('PATH', os.path.join(sdk_dir, 'bin')))
    
    # add the data
    for variable, directory in env_tuple_list:
        env.PrependENVPath(variable, directory)


# TODO(sgk):  currently unused; remove?
def get_cur_sdk_dir_from_reg():
    """Try to find the platform sdk directory from the registry.

    Return None if failed or the directory does not exist"""
    if not SCons.Util.can_read_reg:
        debug('SCons cannot read registry')
        return None

    try:
        val = read_reg(_CURINSTALLED_SDK_HKEY_ROOT)
        debug("Found current sdk dir in registry: %s" % val)
    except WindowsError, e:
        debug("Did not find current sdk in registry")
        return None

    if not os.path.exists(val):
        debug("Current sdk dir %s not on fs" % val)
        return None

    return val


def detect_sdk(version=None):
    if version is None:
        return (len(get_installed_sdks()) > 0)
    return get_installed_sdks().has_key(sdk.version)

def set_sdk_by_version(env, mssdk):
    if not SupportedSDKMap.has_key(mssdk):
        msg = "SDK version %s is not supported" % repr(mssdk)
        raise SCons.Errors.UserError, msg
    get_installed_sdks()
    sdk = InstalledSDKMap.get(mssdk)
    if not sdk:
        msg = "SDK version %s is not installed" % repr(mssdk)
        raise SCons.Errors.UserError, msg
    set_sdk_by_directory(env, sdk.get_sdk_dir(),sdk.has_atlmfc)

def set_default_sdk(env, msver):
    """Set up the default Platform/Windows SDK."""
    #version 9.0 or better is already confired correctly
    if float(msver) < 9.0:
        sdks = get_installed_sdks()
        if len(sdks) > 0:
            set_sdk_by_directory(env, sdks[0].get_sdk_dir())

def setup_sdk_env(env,version=None,target_arch=None,use_script=False,**kw):
    if env.has_key('HOST_SYSTEM') == False:
        env['HOST_SYSTEM'] = part_compat.system_config()
    if env.has_key('TARGET_SYSTEM') == False:
        env['TARGET_SYSTEM'] = part_compat.system_config()
        if target_arch!=None:
            env['TARGET_SYSTEM'].Architecture=target_arch
        elif env.has_key('MS_ARCH'):
            env['TARGET_SYSTEM'].Architecture=env.has_key('MS_ARCH')
    
    if use_script==False:
        # point to a custom location, or non-supported SDK
        if env.has_key('MSSDK_DIR'):
            tmp=env.has_key('MSSDK_DIR')
            if os.path.isdir(tmp):
                set_sdk_by_directory(env, env.subst('$MSSDK_DIR'))
                return
        
        # if not given in tool
        if version==None:
            # see if it was indirect
            if env.has_key('MSSDK_VERSION'):
                #if so use that version
                set_sdk_by_version(env, env.subst('$MSSDK_VERSION'))
                return
            version=env.get('MSVS_VERSION','0.0')
            set_default_sdk(env, version) 
            return 

        set_sdk_by_version(env, version)
        
    elif use_script==True:
        pass 
    elif SCons.Util.is_String(ts.use_script):
        pass
    else:
        raise ValueError("use_script must be a True, False or string path to the script to run")
        pass


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
