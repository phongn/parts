
import SCons.Util 
import parts.common 
import Finders
import os
import parts.pieces.merge_script as merge_script

               
                
       
   
    
class ToolInfo:
    def __init__(self,version,install_scanner,script,subst_vars,shell_vars,test_file):
        # version of the tools this object refers to
        self.version=version
        
        # list of objects or a scanner object that test for finding the root path
        self.install_root=install_scanner
        
        # list of objects that test and handle script processing
        self.script=parts.common.make_list(script)
        
        # the dictionary of value we need to add for correct subsitution of 
        # final value for the enviroment.. ignored in cases of script handling
        self.subst_vars=subst_vars
        
        #The dictionary of values we want to add to the running environment
        # keys() used for script handling
        self.shell_vars=shell_vars
        
        #The file we use to test for a correctly setup envionrment
        self.test_file=test_file
        
        self.shell_cache={}
    
    def version_set(self):
        return [self.version]

    def get_script(self,env):
        for i in self.script:
            ret=i(env)
            if ret is not None:
                return (ret,i.args)
        return None

    def get_root(self,version):

        if SCons.Util.is_List(self.install_root):
            for i in self.install_root:
                ret=i()
                if ret is not None:
                    return os.path.normpath(ret)
        else:
            return self.install_root.resolve(version)
        # no root was found 
        # this is probally an error
        return None

    def get_shell_env(self,env,namespace,version,install_root,script):
        ret={}
        try:
            return self.shell_cache[str(version)+str(install_root)+str(script)]
        except KeyError:
            if SCons.Util.is_String(script):
                # process the script directly
                if os.path.exists(script):
                    ret=merge_script.get_script_env(env,script)
                else:
                    # error as no file exits   
                    pass
            elif script==True:
                #get the default script if one exists and use it
                if install_root is None:
                    # get the install_root
                    install_root=self.get_root(version)
                env[namespace]=parts.common.namespace(env,
                    INSTALL_ROOT=install_root,
                    VERSION=version,
                    **self.subst_vars)
                script_data=self.get_script(env)
                if script_data is None:
                    # we have an error as sccript was not found
                    print "ERROR .. raise user error here"
                    return None
                ret=merge_script.get_script_env(env,script_data[0],script_data[1])
                
            else: # script is False
                if install_root is None:
                    # get the install_root
                    install_root=self.get_root(version)
                shell_env=self.shell_vars
                env[namespace]=parts.common.namespace(env,
                    INSTALL_ROOT=install_root,
                    VERSION=version,
                    TEST='${MSVC.VCINSTALL}',
                    **self.subst_vars)
                
                # subst data
                for k, v in shell_env.items():
                    ret[k]=os.path.normpath(env.subst(v))
        self.shell_cache[str(version)+str(install_root)+str(script)]=ret
        return ret

    def query(self,env,namespace,root_path,use_script):
        
        if SCons.Util.is_List(self.install_root) or SCons.Util.is_String(use_script):
            tmp=self.exists(env,namespace,self.version,root_path,use_script)
            if tmp is None:
                return None
            return {
                self.version:
                tmp
            }
        return self.install_root.scan()

    ## general case
    def exists(self,env,namespace,version,root_path,use_script):
        shell_env=self.get_shell_env(env,namespace,version,root_path,use_script)
        try:
            tpath=shell_env['PATH']
            #print "tpath=",tpath
            tmp=SCons.Util.WhereIs(self.test_file,path=tpath)
            #print tmp
            if tmp is not None:
                #print "FOUND"
                return shell_env
        except:
            print "ERROR! exception hit"
            pass
        #print "NOT FOUND"
        return None


  ####  
    ##.. special MS case
    def _exists(self,tool,strict_64=False):
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




    
    
    
    
