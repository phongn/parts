import os.path
import os
import SCons.Util


ctc_action = SCons.Action.Action('$CTC_COM', '$CTC_COMSTR')
ctc_builder = SCons.Builder.Builder(action=ctc_action,
                                    src_suffix='.ctc',
                                    suffix='.cto',
                                    src_builder=[],
                                    source_scanner=SCons.Tool.SourceFileScanner)
SCons.Tool.SourceFileScanner.add_scanner('.ctc', SCons.Defaults.CScan)


def generate(env, version=None, abi=None, topdir=None, verbose=0):

    ver_lst=[]
    ver=str(version)
    keyname = 'SOFTWARE\\Microsoft\\VisualStudio\\VSIP'
    val=None
    try: 
        if version != None:
            (val,temp) = SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, 
                keyname+'\\'+ver+'\\'+'InstallDir')
    except SCons.Util.RegError:
        version=None
            
    if version == None:
        try:
            if version==None:
                k = SCons.Util.RegOpenKeyEx (SCons.Util.HKEY_LOCAL_MACHINE, keyname)
                try:
                    i=0
                    while 1:
                        subkey = SCons.Util.RegEnumKey(k, i)
                        ver_lst.append(subkey)
                        i=i+1
                # no more subkeys
                except EnvironmentError:
                    pass
                
                # need to clean this up later
                # need to add better sort function logic
                ver_lst.sort()
                ver_lst.reverse()
                if ver_lst != []:
                    version=ver_lst[0]
        except SCons.Util.RegError:
            raise SCons.Errors.UserError, \
                      "Failed to find VSIP registry key, looked for key: %s "%keyname 
                
        try: 
            if version != None:
                (val,temp) = SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, 
                    keyname+'\\'+version+'\\'+'InstallDir')
        except SCons.Util.RegError:
            version=None
            
    if version == None:
        raise SCons.Errors.UserError, \
                  "Failed to find VSIP %s: "%ver + \
                  "installed versions are %s"%(', '.join(ver_lst))
    
    include_path=[os.path.join(val,'VisualStudioIntegration\\Common\\Inc'),
        os.path.join(val,'VisualStudioIntegration\\Common\\IDL'),
        os.path.join(val,'VisualStudioIntegration\\Common\\Inc\\office10')]
    
    env_path=[os.path.join(val,'VisualStudioIntegration'),os.path.join(val,'VisualStudioIntegration\\Tools\\Bin')]
    
    if env.get('CONFIG','release')=='debug':
        env_libpath=[os.path.join(val,'VisualStudioIntegration\\Common\\lib\\debug')]
    else:
        env_libpath=[os.path.join(val,'VisualStudioIntegration\\Common\\lib\\retail')]

    env['VSIP_ROOT']=val

    env.PrependENVPath('INCLUDE', include_path)
    env.PrependENVPath('LIB', env_libpath)
    env.PrependENVPath('PATH', env_path)   
    
    if verbose==True:
        print "Found VSIP version",version,"found at",val 
    
    env['INCPREFIX']  = '/I'
    env['INCSUFFIX']  = ''
    env['_CTC_INCFLAGS'] = '$( ${_concat(INCPREFIX, CTC_INCLUDES, INCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['CTC']='ctc'
    env['CTC_INCLUDES']=[os.path.join(val,'VisualStudioIntegration\\Common\\Inc'),os.path.join(val,'VisualStudioIntegration\\Common\\Inc\\office10')]
    env['CTC_FLAGS']=['-nologo','-Ccl']
    env['CTC_COM'] = '$CTC $SOURCE $TARGET $CTC_FLAGS $_CTC_INCFLAGS'
    env['BUILDERS']['CTC'] = ctc_builder
        
    
    
##    try: 
##        (vsipInstallDir, temp) = SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\VisualStudio\VSIP\7.1\InstallDir')
##        include_path = os.path.join (vsipInstallDir, 'EnvSDK', 'common', 'idl') + os.pathsep + os.path.join (vsipInstallDir, 'EnvSDK', 'common', 'inc') + os.pathsep + os.path.join (vsipInstallDir, 'EnvSDK', 'common', 'inc', 'office10') + os.pathsep
##        bin_path = os.path.join (vsipInstallDir, 'EnvSDK', 'tools', 'bin', 'x86') + os.pathsep
##        env.PrependENVPath('INCLUDE', include_path)
##        env.PrependENVPath('PATH', bin_path)
##
##    except SCons.Util.RegError:
##        print 'Failed to find VSIP ' + str (version)
##        os.abort ()
##        pass


def exists (env):
    try:
        # this is currently the only version I know about, but there is a newer version too
        SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\VisualStudio\VSIP\7.1\InstallDir')
        return 1
    except SCons.Util.RegError:
        return 0
