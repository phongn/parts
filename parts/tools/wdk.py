import os
import SCons.Util

def generate(env, version=None, abi=None, verbose=0):
    ver_lst=[]
    ver=str(version)
    keyname = 'SOFTWARE\\Microsoft\\WINDDK'
    val=None
    try: 
        if version != None:
            (val,temp) = SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, 
                keyname+'\\'+ver+'\\'+'LFNDirectory')
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
                ver_lst.sort()
                if ver_lst != []:
                    version=ver_lst[0]
        except SCons.Util.RegError:
            raise SCons.Errors.UserError, \
                      "Failed to find WDK registry key, looked for key: %s "%keyname 
                
        try: 
            if version != None:
                (val,temp) = SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, 
                    keyname+'\\'+version+'\\'+'LFNDirectory')
        except SCons.Util.RegError:
            version=None
            
    if version == None:
        raise SCons.Errors.UserError, \
                  "Failed to find WDK %s: "%ver + \
                  "installed versions are %s"%(', '.join(ver_lst))
    
    env['WDKINSTALLDIR']=val
    env['WDKROOTINCLUDE']=val+'\\'+'inc'
    env['WDKROOTLIB']=val+'\\'+'lib'
    
    if verbose==True:
        print "Found WDK version",version,"found at",val
        

def exists (env):
    try:
        # this is currently the only version I know about, but there is a newer version too
        SCons.Util.RegGetValue (SCons.Util.HKEY_LOCAL_MACHINE, r'SOFTWARE\\Microsoft\\WINDDK')
        return 1
    except SCons.Util.RegError:
        return 0
