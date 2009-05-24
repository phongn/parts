
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
        
        #state value for when we add data to the tool setting object
        # this allow use to make sure we overide certain toolinfo objects
        # when the host they are bound to is native over item that are not
        self.is_native=False
    
    def version_set(self):
        return [self.version]
    
    def make_ver_shell_env_set(self,ver,env):
        ret={}
        tmp=ver.split('.')
        for i in range (0,len(tmp)):
            # add path data
            ret[".".join(tmp[:i+1])]=env
        return ret

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
        if install_root is None:
            # get the install_root
            install_root=self.get_root(version)
        #Setup namespaced varibles
        env[namespace]=self.get_namespace(env,
            INSTALL_ROOT=install_root,
            VERSION=version)
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
                script_data=self.get_script(env)
                if script_data is None:
                    # we have an error as sccript was not found
                    print "ERROR .. raise user error here"
                    return None
                ret=merge_script.get_script_env(env,script_data[0],script_data[1])
                
            else: # script is False
                # subst data
                for k, v in self.shell_vars.items():
                    ret[k]=os.path.normpath(env.subst(v))
                    
        self.shell_cache[str(version)+str(install_root)+str(script)]=ret
        return ret

    def get_namespace(self,env,**kw):
        kw.update(self.subst_vars)
        return parts.common.namespace(env,
                    **kw)

    def query(self,env,namespace,root_path,use_script):
        
        if SCons.Util.is_List(self.install_root) or SCons.Util.is_String(use_script):
            found={self.version:root_path}
        else:
            found=self.install_root.scan()
        
        if found is None:
            return None

        ret={}
        for v,p in found.items():
            tmp=self.exists(env,namespace,v,p,use_script)
            if tmp is not None:
                ret.update(self.make_ver_shell_env_set(v,tmp))
        return ret

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




    
    
    
    
