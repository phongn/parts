

## todo hack this class up
class VisualStudio:
    """
    An abstract base class for trying to find installed versions of
    Visual Studio.
    """
    def __init__(self, version, **kw):
        # teh version of this objects
        self.version=version
        # Meta-data add varaible a memebers
        self.__dict__.update(kw)
        # cache of data
        self._cache = {}
        
    def get_path(self):
        if self.__dict__.has_key('path_cache')==True:
            return self.path_cache
        dict={
            'VCINSTALL':rootpath.msvc_root_dir(version),
            'VSINSTALL':rootpath.msvs_root_dir(version),
            'FRAMEWORK_ROOT':rootpath.framework_root(),
            'FRAMEWORK_ROOT64':rootpath.framework_root64()
            }
        s=vcbin_arch()+\
            vcbin()+\
            vcpackage()+\
            vs_ide()+\
            common_tools()+\
            common_tools_bin()+\
            frameworks_sdk_bin()
        self.path_cache+=_subst_(s,dict)
        return self.path_cache
    
    def get_include(self):
        if self.__dict__.has_key('include_cache')==True:
            return self.include_cache
        dict={
            'VCINSTALL':rootpath.msvc_root_dir(version),
            'VSINSTALL':rootpath.msvs_root_dir(version),
            'FRAMEWORK_ROOT':rootpath.framework_root(),
            'FRAMEWORK_ROOT64':rootpath.framework_root64()
            }
        s=  atlmfc_include()+\
            crt_include()+\
            platformsdk_include()+\
            framework_include()
        self.include_cache+=_subst_(s,dict)
        return self.include_cache
        
    def get_lib(self):
        
        if self.__dict__.has_key('lib_cache')==True:
            return self.lib_cache
        dict={
            'VCINSTALL':rootpath.msvc_root_dir(version),
            'VSINSTALL':rootpath.msvs_root_dir(version),
            'FRAMEWORK_ROOT':rootpath.framework_root(),
            'FRAMEWORK_ROOT64':rootpath.framework_root64()
            }
        s=  atlmfc_lib()+\
            crt_lib()+\
            platformsdk_lib()+\
            frameworks_sdk_lib()
        self.lib_cache+=_subst_(s,dict)
        return self.lib_cache
    
    def get_libpath(self):
        
        if self.__dict__.has_key('libpath_cache')==True:
            return self.libpath_cache
        dict={
            'VCINSTALL':rootpath.msvc_root_dir(version),
            'VSINSTALL':rootpath.msvs_root_dir(version),
            'FRAMEWORK_ROOT':rootpath.framework_root(),
            'FRAMEWORK_ROOT64':rootpath.framework_root64()
            }
        s=  atlmfc_lib()+\
            platformsdk_lib()+\
            frameworks_sdk_lib()
        self.libpath_cache+=_subst_(s,dict)
        return self.libpath_cache
    
    # path functions
    def common_tools(self):
        ret='${VSINSTALL}Common7\\Tools\\bin'+';'
        if self.version=='6.0':
            ret='${VSINSTALL}Common\\TOOLS\\'+';'
        return ret

    def common_tools_bin(self):
        ret='${VSINSTALL}Common7\\Tools'+';'
        if self.version=='6.0':
            ret='${VSINSTALL}Common\\TOOLS\\WINNT'+';'
        return ret

    def vs_ide(self):
        ret='${VSINSTALL}Common7\\IDE'+';'
        if self.version=='6.0':
            ret='${VSINSTALL}Common\\msdev98\\BIN'+';'
        return ret

    def vcbin(self):
        ret='${VCINSTALL}BIN'+';'
        return ret

    def vcpackage(self):
        ret='${VCINSTALL}VCPackages'+';'
        if self.version=='6.0':
            ret=''
        return ret

    def vcbin_arch(self):
        ''' 
        returns the arch bin path case or empty string
        currently we only handle the x86_64 case,
        can add the x64 case here if needed
        '''
        ret=''
        host=common.ChipArchitecture()
        if self.target_arch == 'x86_64' and common.is_win64():
            # it just easier this way... try native then cross in path
            ret = '${VCINSTALL}BIN\\amd64'+';'+'${VCINSTALL}BIN\\x86_amd64'+';'
        elif self.target_arch == 'x86_64' and common.is_win64()==False:
            ret = '${VCINSTALL}BIN\\x86_amd64'+';'
        return ret
    
    # include path functions
    def atlmfc_include(self):
        ret=''
        if self.version=='6.0' :
            ret='${VCINSTALL}ATL\\INCLUDE'+';'+'${VCINSTALL}MFC\\INCLUDE'+';'
        else:
            ret='${VCINSTALL}ATLMFC\\INCLUDE'+';'
        return ret

    def crt_include(self):
        ret='${VCINSTALL}INCLUDE'+';'
        return ret    

    def platformsdk_include(self,use_sdk=False):
        ''' this will try to update the platform SDK
        to the best SDK version if one is installed
        and the use_sdk is true
        '''
        ret=''
        
        # get the current SDK root based on a req key
        # need for vc 9.0 and newer
        sdk_root=rootpath.get_current_sdk()
        
        if use_sdk==False:
            # use default values
            if self.version== '6.0':
                #For this version it is already in the crt_include()
                ret=''
            elif self.version== '7.0':
                ret=''
            elif self.version== '7.1':
                ret='${VCINSTALL}PlatformSDK\\include'+';'
            elif self.version== '8.0':
                ret='${VCINSTALL}PlatformSDK\\include'+';'
            elif self.version== '9.0':
                ret=sdk_root+'include'+';'
        return ret    
    def framework_include(self):
        ''' This returns the include path need for the framework SDK
        However this is not needed in newer VC drops'''
        ret=''
        
        if self.version == '7.0':
            pass
        elif self.version == '7.1':
            ret = '${VSINSTALL}SDK\\v1.1\\bin'+';'
        elif self.version == '8.0':
            ret = '${VSINSTALL}SDK\\v2.0\\bin'+';'
        return ret
    
    #lib path functions
    
    def atlmfc_lib(self):
        ret=''
        if self.version=='6.0' and self.target_arch=='x86':
            ret='${VCINSTALL}MFC\\LIB'+';'
        elif self.version=='7.0' and self.target_arch=='x86':
            ret='${VCINSTALL}ATLMFC\\LIB'+';'
        elif self.version=='7.1' and self.target_arch=='x86':
            ret='${VCINSTALL}ATLMFC\\LIB'+';'
        elif self.version=='8.0' and self.target_arch=='x86':
            ret='${VCINSTALL}ATLMFC\\LIB'+';'
        elif self.version=='8.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}ATLMFC\\LIB\\amd64'+';'
        elif self.version=='9.0' and self.target_arch=='x86':
            ret='${VCINSTALL}ATLMFC\\LIB'+';'
        elif self.version=='9.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}ATLMFC\\LIB\\amd64'+';'

        return ret

    def crt_lib(self):
        ret=''
        if self.version=='8.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}LIB\\amd64'+';'
        elif self.version=='9.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}LIB\\amd64'+';'
        else:
            ret='${VCINSTALL}LIB'+';'
        return ret
    
    def platformsdk_lib(self,use_sdk=False):
        ''' 
        This will try to update the platform SDK
        to the best SDK version if one is installed
        and the use_sdk is true
        '''    
        ret=''
        
        # get the current SDK root based on a req key
        # need for vc 9.0 and newer
        sdk_root=rootpath.get_current_sdk()
        
        if use_sdk==False:
            # use default values
            if self.version== '6.0' and self.target_arch=='x86':
                #For this version it is already in the crt_include()
                ret=''
            elif self.version== '7.0'and self.target_arch=='x86':
                ret=''
            elif self.version== '7.1'and self.target_arch=='x86':
                ret='${VCINSTALL}PlatformSDK\\lib'+';'
            elif self.version== '8.0'and self.target_arch=='x86':
                ret='${VCINSTALL}PlatformSDK\\lib'+';'
            elif self.version== '8.0'and self.target_arch=='x86_64':
                ret='${VCINSTALL}PlatformSDK\\lib\\amd64'+';'
            elif self.version== '9.0'and self.target_arch=='x86':
                ret=sdk_root+'lib'+';'
            elif self.version== '9.0'and self.target_arch=='x86_64':
                ret=sdk_root+'lib\\amd64'+';'
        return ret

    def frameworks_sdk_lib(self):
        ret=''
        if self.version=='7.0' and self.target_arch=='x86':
            ret=''
        elif self.version=='7.1' and self.target_arch=='x86':
            ret='${VSINSTALL}SDK\\v1.1\\lib'+';'
        elif self.version=='8.0' and self.target_arch=='x86':
            ret='${VSINSTALL}SDK\\v2.0\\lib'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
        elif self.version=='8.0' and self.target_arch=='x86_64':
            ret='${VSINSTALL}SDK\\v2.0\\lib\AMD64'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
        elif self.version=='9.0' and self.target_arch=='x86':
            ret='${FRAMEWORK_ROOT}v3.5'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
        elif self.version=='9.0' and self.target_arch=='x86_64':
            ret='${FRAMEWORK_ROOT64}v3.5'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
        return ret

# core path functions

    def get_msvc_reg_root(self):
        ''' 
        gets the roots msvc path, based on version
        version is a float from 6.0 or better (up to 9.0 currently)
        returns None if we can find this version in the registry
        '''
        
        # make sure we can read
        if not SCons.Util.can_read_reg:
            debug('SCons cannot read registry')
            return None
        
        # currently VS is a 32-bit app. so on any 64-bit Windows installs
        # we need to modify the path we look for information in the registry
        HKEY_ARCH="\\"
        if common.is_win64():
            HKEY_ARCH="\\Wow6432Node\\"
        comps=''
        for key in self.hkey_root_vc:
            key=key % (HKEY_ARCH)
            try:
                comps = common.read_reg(key)
                debug('Found VC dir in registry: %s' % comps)
                break
            except WindowsError, e:
                debug('Did not find VC dir key %s in registry' % \
                      (comps))
                comps=None
        
        # reg value with 6.0 is different from rest of VS versions
        # this cleans up path to end with slashes
        if ('6.0' == self.version) and comps!=None:
            comps+='\\'
        return comps


    def msvc_env_root(self):
        '''
        Get the version information via reading the VSXXCOMNTOOLS variable
        Where XX is the a value like 70,80,90
        
        note that vc 6.0 does not support this, in this case this always fails
        todo.. fix that user can make 6.0 work
        '''
        d = os.environ.get(self.common_tools_var, None)

        pdir = None
        if d:
            debug('Varible %s not found' % (self.common_tools_var))
        elif os.path.isdir(d):
            debug('Found varible %s with value of %s exists' % (self.common_tools_var,d))
            pdir=d[:-14]+self.vc_sub_dir
        else:
            debug('Path value of %s for varible of %s does not exists' % (d,self.common_tools_var))
            
        return pdir
       

    def msvc_default_root(self):
        ''' returns known default paths, incase the reg or env fails'''
        ret=self.default_install_vc % program_files_dir()
        return ret

    def msvs_default_root(self):
        ''' returns known default paths, incase the reg or env fails'''
        ret=self.msvc_default_root()
        if ret != None:
            ret= ret[:-len(self.vc_sub_dir)]
        return ret

    def msvs_root_dir(self):
        ''' 
        Get the root MSVS install directory for a given version
        return None if there is an error
        '''

        if self.__dict__.has_key('msvs_root_dir_cache')==True:
            return self.msvs_root_dir_cache
        val=msvc_root_dir()
        if val != None:
            val= val[:-len(self.vc_sub_dir)]
            if os.path.isdir(val)==False:
                self.msvs_root_dir_cache=None
                return None

        self.msvs_root_dir_cache=val
        return val

    def msvc_root_dir(self):
        ''' 
        Get the root MSVC install directory for a given version
        return None if there is an error
        '''
        if self.__dict__.has_key('msvc_root_dir_cache') == True:
            return self.msvc_root_dir_cache 
        val=msvc_reg_root()
        if val == None or os.path.isdir(val)==False:
            val=msvc_env_root()
            if val == None or os.path.isdir(val)==False:
                val=msvc_default_root()
                if val == None or os.path.isdir(val)==False:
                    self.msvc_root_dir_cache = None
                    return None

        self.msvc_root_dir_cache =val
        return val

    def find_batch_file(self):
        """Try to find the Visual Studio or Visual C/C++ batch file.

        Return None if failed or the batch file does not exist.
        """
        pdir = self.msvc_root_dir()
        if not pdir:
            debug('find_batch_file():  no pdir')
            return None

        host=common.ChipArchitecture()
        if self.target_arch == 'x86_64' and host=='x86_64':
            batch_file = pdir+'bin\\amd64\\'+self.batch_file
            if not os.path.isfile(batch_file):
                batch_file = pdir+'bin\\x86_amd64\\'+self.batch_file
        elif self.target_arch == 'x86_64' and host=='x86':
            batch_file = pdir+'bin\\x86_amd64\\'+self.batch_file
        elif self.target_arch == 'ia64' and host=='ia64':
            batch_file = pdir+'bin\\ia64\\'+self.batch_file
            # these systems should have a 32-bit emulator
            # shipped in the OS..may need to double check this...
            if not os.path.isfile(batch_file):
                batch_file = pdir+'bin\\x86_ia64\\'+self.batch_file
        elif self.target_arch == 'ia64':
            batch_file = pdir+'bin\\x86_ia64\\'+self.batch_file
        elif self.target_arch == 'x86':
            batch_file = pdir+'bin\\'+self.batch_file
        else:
            batch_file=''

        if not os.path.isfile(batch_file):
            debug('find_batch_file():  %s not on file system' % batch_file)
            return None
        return batch_file

    def batch_file(self):
        if self.__dict__.has_key('batch_file_cache')==True:
            return self.batch_file_cache
        batch_file = self.find_batch_file()
        self.batch_file_cache = batch_file
        return self.batch_file_cache
