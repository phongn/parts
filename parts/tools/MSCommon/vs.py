import SCons.Util
from common import debug
import common,os,part_compat

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
        
    def get_shell_enviroment(self):
        '''this function returns the shell environment for a give version and architecture
        '''
        if self.__dict__.has_key('shellenv_cache')==True:
            return self.shellenv_cache
        shellenv={
        'PATH':     self.get_path(),
        'INCLUDE':  self.get_include(),
        'LIB':      self.get_lib(),
        'LIBPATH':  self.get_libpath()
        }
        self.shellenv_cache=shellenv
        return self.shellenv_cache

    def get_path(self):
        if self.__dict__.has_key('path_cache')==True:
            return self.path_cache
        dict={
            'VCINSTALL':self.msvc_root_dir(),
            'VSINSTALL':self.msvs_root_dir(),
            'FRAMEWORK_ROOT':self.framework_root(),
            'FRAMEWORK_ROOT64':self.framework_root64()
            }
        s=  self.vcbin_arch()+\
            self.vcbin()+\
            self.platformsdk_bin_arch()+\
            self.platformsdk_bin()+\
            self.vcpackage()+\
            self.vs_ide()+\
            self.common_tools()+\
            self.common_tools_bin()+\
            self.frameworks_sdk_bin()
        self.path_cache=common._subst_(s,dict)
        return self.path_cache
    
    def get_include(self):
        if self.__dict__.has_key('include_cache')==True:
            return self.include_cache
        dict={
            'VCINSTALL':self.msvc_root_dir(),
            'VSINSTALL':self.msvs_root_dir(),
            'FRAMEWORK_ROOT':self.framework_root(),
            'FRAMEWORK_ROOT64':self.framework_root64()
            }
        s=  self.atlmfc_include()+\
            self.crt_include()+\
            self.platformsdk_include()+\
            self.framework_include()
        self.include_cache=common._subst_(s,dict)
        return self.include_cache
        
    def get_lib(self):
        
        if self.__dict__.has_key('lib_cache')==True:
            return self.lib_cache
        dict={
            'VCINSTALL':self.msvc_root_dir(),
            'VSINSTALL':self.msvs_root_dir(),
            'FRAMEWORK_ROOT':self.framework_root(),
            'FRAMEWORK_ROOT64':self.framework_root64()
            }
        s=  self.atlmfc_lib()+\
            self.crt_lib()+\
            self.platformsdk_lib()+\
            self.frameworks_sdk_lib()
        self.lib_cache=common._subst_(s,dict)
        return self.lib_cache
    
    def get_libpath(self):
        
        if self.__dict__.has_key('libpath_cache')==True:
            return self.libpath_cache
        dict={
            'VCINSTALL':self.msvc_root_dir(),
            'VSINSTALL':self.msvs_root_dir(),
            'FRAMEWORK_ROOT':self.framework_root(),
            'FRAMEWORK_ROOT64':self.framework_root64()
            }
        s=  self.atlmfc_lib()+\
            self.platformsdk_lib()+\
            self.frameworks_sdk_lib()
        self.libpath_cache=common._subst_(s,dict)
        return self.libpath_cache
    
    # path functions
    def common_tools(self):
        ret='${VSINSTALL}Common7\\Tools\\bin'+';'
        if self.version=='6.0':
            ret='${VSINSTALL}Common\\TOOLS\\'+';'
        if self.version=='9.0':
            ret=''
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
        host=part_compat.ChipArchitecture()
        if self.target_arch == 'x86_64' and common.is_win64():
            # it just easier this way... try native then cross in path
            ret = '${VCINSTALL}BIN\\amd64'+';'+'${VCINSTALL}BIN\\x86_amd64'+';'
        elif self.target_arch == 'x86_64' and common.is_win64()==False:
            ret = '${VCINSTALL}BIN\\x86_amd64'+';'
        elif self.target_arch == 'ia64' and common.is_win64()==True:
            ret = '${VCINSTALL}BIN\\ia64'+';'
        elif self.target_arch == 'ia64' and common.is_win64()==False:
            ret = '${VCINSTALL}BIN\\x86_ia64'+';'
        return ret

    def platformsdk_bin(self):
        
        ret=''
        
        # get the current SDK root based on a req key
        # need for vc 9.0 and newer
        sdk_root=self.get_current_sdk()
        
        # use default values
        if self.version== '6.0' and self.target_arch=='x86':
            #For this version it is already in the crt_include()
            ret=''
        elif self.version== '9.0':
            ret=sdk_root+'bin'+';'
            
        return ret
    
    def platformsdk_bin_arch(self):
        
        ret=''
        
        # get the current SDK root based on a req key
        # need for vc 9.0 and newer
        sdk_root=self.get_current_sdk()
        
        # use default values
        if self.version== '6.0' and self.target_arch=='x86':
            #For this version it is already in the crt_include()
            ret=''
        elif self.version== '9.0'and self.target_arch=='x86':
            ret=sdk_root+'lib'+';'
        elif self.version== '9.0'and self.target_arch=='x86_64':
            ret=sdk_root+'bin\\x64'+';'
        elif self.version== '9.0'and self.target_arch=='ia64':
            ret=sdk_root+'bin\\ia64'+';'
            
        return ret    
    
    def frameworks_sdk_bin(self):
        ret=''
        if self.version=='7.0' and self.target_arch=='x86':
            ret=''
        elif self.version=='7.1' and self.target_arch=='x86':
            ret='${VSINSTALL}SDK\\v1.1\\bin'+';'+'${FRAMEWORK_ROOT}v1.1.4322'+';'
        elif self.version=='8.0' and self.target_arch=='x86':
            ret='${VSINSTALL}SDK\\v2.0\\bin'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
        elif self.version=='8.0' and self.target_arch=='x86_64':
            ret='${VSINSTALL}SDK\\v2.0\\bin'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
        elif self.version=='9.0' and self.target_arch=='x86':
            ret='${FRAMEWORK_ROOT}v3.5'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
        elif self.version=='9.0' and self.target_arch=='x86_64':
            ret='${FRAMEWORK_ROOT64}v3.5'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
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

    def platformsdk_include(self):
        
        ret=''
        
        # get the current SDK root based on a req key
        # need for vc 9.0 and newer
        sdk_root=self.get_current_sdk()
        
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
        elif self.version=='8.0' and self.target_arch=='ia64':
            ret='${VCINSTALL}ATLMFC\\LIB\\ia64'+';'
        elif self.version=='9.0' and self.target_arch=='x86':
            ret='${VCINSTALL}ATLMFC\\LIB'+';'
        elif self.version=='9.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}ATLMFC\\LIB\\amd64'+';'
        elif self.version=='9.0' and self.target_arch=='ia64':
            ret='${VCINSTALL}ATLMFC\\LIB\\ia64'+';'

        return ret

    def crt_lib(self):
        ret=''
        if self.version=='8.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}LIB\\amd64'+';'
        elif self.version=='8.0' and self.target_arch=='ia64':
            ret='${VCINSTALL}LIB\\ia64'+';'
        elif self.version=='9.0' and self.target_arch=='x86_64':
            ret='${VCINSTALL}LIB\\amd64'+';'
        elif self.version=='9.0' and self.target_arch=='ia64':
            ret='${VCINSTALL}LIB\\ia64'+';'
        else:
            ret='${VCINSTALL}LIB'+';'
        return ret
    
    def platformsdk_lib(self):
        
        ret=''
        
        # get the current SDK root based on a req key
        # need for vc 9.0 and newer
        sdk_root=self.get_current_sdk()
        
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
        elif self.version== '8.0'and self.target_arch=='ia64':
            ret='${VCINSTALL}PlatformSDK\\lib\\ia64'+';'
        elif self.version== '9.0'and self.target_arch=='x86':
            ret=sdk_root+'lib'+';'
        elif self.version== '9.0'and self.target_arch=='x86_64':
            ret=sdk_root+'lib\\x64'+';'
        elif self.version== '9.0'and self.target_arch=='ia64':
            ret=sdk_root+'lib\\ia64'+';'
            
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
        elif self.version=='8.0' and self.target_arch=='ia64':
            ret='${VSINSTALL}SDK\\v2.0\\lib\ia64'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
        elif self.version=='9.0' and self.target_arch=='x86':
            ret='${FRAMEWORK_ROOT}v3.5'+';'+'${FRAMEWORK_ROOT}v2.0.50727'+';'
        elif self.version=='9.0' and self.target_arch!='x86':
            ret='${FRAMEWORK_ROOT64}v3.5'+';'+'${FRAMEWORK_ROOT64}v2.0.50727'+';'
        return ret

# core path functions

    def msvc_reg_root(self):
        ''' 
        gets the roots msvc path, based on version
        version is a str from 6.0 or better (up to 9.0 currently)
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
        if d==None:
            debug('Varible %s not found' % (self.common_tools_var))
        elif os.path.isdir(d):
            debug('Found varible %s with value of %s exists' % (self.common_tools_var,d))
            pdir=d[:-14]+self.vc_sub_dir
        else:
            debug('Path value of %s for varible of %s does not exists' % (d,self.common_tools_var))
            
        return pdir
       

    def msvc_default_root(self):
        ''' returns known default paths, incase the reg or env fails'''
        ret=self.default_install_vc % common.program_files_dir()
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
        val=self.msvc_root_dir()
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
        val=self.msvc_reg_root()
        if val == None or os.path.isdir(val)==False:
            val=self.msvc_env_root()
            if val == None or os.path.isdir(val)==False:
                val=self.msvc_default_root()
                if val == None or os.path.isdir(val)==False:
                    self.msvc_root_dir_cache = None
                    return None

        self.msvc_root_dir_cache =val
        return val

#batch file handling
    def find_batch_file(self):
        """Try to find the Visual Studio or Visual C/C++ batch file.

        Return None if failed or the batch file does not exist.
        """
        pdir = self.msvc_root_dir()
        if not pdir:
            debug('find_batch_file():  no pdir')
            return None

        host=part_compat.ChipArchitecture()
        if self.target_arch == 'x86_64' and host=='x86_64':
            batch_file = pdir+'bin\\amd64\\'+self.batch_file_base+'amd64.bat'
            if not os.path.isfile(batch_file):
                batch_file = pdir+'bin\\x86_amd64\\'+self.batch_file_base+'x86_amd64.bat'
        elif self.target_arch == 'x86_64' and host=='x86':
            batch_file = pdir+'bin\\x86_amd64\\'+self.batch_file_base+'x86_amd64.bat'
        elif self.target_arch == 'ia64' and host=='ia64':
            batch_file = pdir+'bin\\ia64\\'+self.batch_file_base+'ia64.bat'
            # these systems should have a 32-bit emulator
            # shipped in the OS..may need to double check this...
            if not os.path.isfile(batch_file):
                batch_file = pdir+'bin\\x86_ia64\\'+self.batch_file_base+'x86_ia64.bat'
        elif self.target_arch == 'ia64':
            batch_file = pdir+'bin\\x86_ia64\\'+self.batch_file_base+'x86_ia64.bat'
        elif self.target_arch == 'x86':
            batch_file = pdir+'bin\\'+self.batch_file_base+'32.bat'
        else:
            batch_file=''
        if not os.path.isfile(batch_file):
            debug('find_batch_file():  %s not on file system' % batch_file)
            return None
        return batch_file

    def get_batch_file(self):
        if self.__dict__.has_key('batch_file_cache')==True:
            return self.batch_file_cache
        batch_file = self.find_batch_file()
        self.batch_file_cache = batch_file
        return self.batch_file_cache


# tool checking
    def cl_exists(self):
        return self.exists('cl',True)
        
    def exists(self,tool,strict_64=False):
        '''
        Tests to see if the tool exist for this version of VS
        Strict_64 enforce the tool lives in the 64 bit directory for the
        given architecture. Not all tool need this on, so it defaults to False
        '''
        
        tmp=SCons.Util.WhereIs(tool,path=self.get_path())
        if tmp!=None:
            # This if block validates that in the case of finding the x86_64
            # version of the tool, we don't get a false positive of a 32-bit version
            # This happens because the path is in the general form of (for 64-bit only)
            # vcbin_arch;vcbin;...   
            # Which means that two CL can exist on the path, but since the vcbin_arch 
            # form is first it is found first. if it was not there or installed we would
            # get a false postive.
            if strict_64==True:
                if self.target_arch == 'x86_64':
                    if tmp.find('amd64') == -1:
                        return False
                elif self.target_arch == 'ia64':
                    if tmp.find('ia64') == -1:
                        return False
            return True
        return False  
      
    def get_current_sdk(self):
        ''' get SDK path based on reg key used for vc 9.0 and newer'''
        # note this key is used for both 32-bit and 64-bit systems
        # this mean the that default path will always be program file/xxx
        # even on 64-bit systems
        key='SOFTWARE\Microsoft\Microsoft SDKs\Windows\CurrentInstallFolder'
        dir=''
        try:
            dir=SCons.Util.RegGetValue(SCons.Util.HKEY_CURRENT_USER, key)[0]
            debug('Found SDK dir in registry: %s' % dir)
        except WindowsError, e:
            debug('Did not find SDK dir key %s in registry' % \
                  (key))
        return dir
    
    def framework_root(self):
        VS_HKEY_BASE="\\"
        comps=''
        if common.is_win64():
            VS_HKEY_BASE="\\Wow6432Node\\"
        key = 'Software%sMicrosoft\\.NETFramework\\InstallRoot' % (VS_HKEY_BASE)
        try:
            comps = common.read_reg(key)
            debug('Found framework dir in registry: %s' % comps)
        except WindowsError, e:
            debug('Did not find framework dir key %s in registry' % \
                  (key))
            return ''
        return comps
        
    def framework_root64(self):
        ''' currently this value when added seem to be messed up in the scripts
        on 32-bit OS systems. Since this path is always bad, we don't add it in these
        cases'''
        comps=''     
        key = 'Software\\Microsoft\\.NETFramework\\InstallRoot'
        try:
            comps = common.read_reg(key)
            if comps[-3:] != '64\\':
                comps=comps[:-1]+'64\\'
                if os.path.exists(comps) == False:
                    debug('Did not find framework64 dir')
                    return ''
            debug('Found framework64 dir in registry: %s' % comps)
        except WindowsError, e:
            debug('Did not find framework64 dir key %s in registry' % \
                  (key))
            return ''
        return comps
