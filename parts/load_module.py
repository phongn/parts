
import sys
import os
import imp
import traceback
import StringIO

import SCons.Errors
import SCons.Script

import glb
import common
import api.output


g_site_dir_cache={}
def get_site_directories(subdir):
    try:
        return g_site_dir_cache[subdir]
    except KeyError:
        if glb._host_sys is None:
            print "host_os bootstrap bug"
            1/0
        host_os=glb._host_sys # can't use HOST_OS because of bootstrap issue.
        syspath=[]
        localpath=[]
        # local data
        localpath=[
            #homedir/.parts-site
            os.path.join(os.path.expanduser('~'),'parts-site',subdir),
            os.path.join(os.path.expanduser('~'),'.parts-site',subdir)
            ]
        # add paths for windows
        if host_os=='win32':
            # if we run as a service ( like running in buildbot) we may not have a user directory
            if  os.environ.has_key('APPDATA'):
                localpath=localpath+[os.path.join(os.environ['APPDATA'],'parts-site',subdir)]
            
            
        # global system area
        if host_os == 'win32':
            # should not be needed.. just being careful
            if  os.environ.has_key('ALLUSERSPROFILE'):
                syspath=[os.path.join(os.environ['ALLUSERSPROFILE'],'parts-site',subdir)]
        elif host_os == 'darwin':
            syspath=[os.path.join('/Library/Application Support/parts','parts-site',subdir)]
        else:
            syspath=[os.path.join('/usr/share/parts','parts-site',subdir)]
        
        
        if SCons.Script.GetOption('use_part_site'):
            sitepaths=[
                os.path.join(os.path.abspath(SCons.Script.GetOption('use_part_site')), subdir),
                # parts install
                os.path.join(glb.parts_path,subdir)
            ]
        elif SCons.Script.GetOption('global_part_site'):
            sitepaths=[
                #current directory parts_site or user pointed site
                os.path.abspath(os.path.join('.','parts-site',subdir)),
                os.path.abspath(os.path.join('.','.parts-site',subdir))
                #homedir/.parts-site
                ]+[
                # user part-site in parts install
                os.path.join(glb.parts_path,'parts-site',subdir),
                # parts install
                os.path.join(glb.parts_path,subdir)
            ]
        else:
            sitepaths=[
                #current directory parts_site or user pointed site
                os.path.abspath(os.path.join('.','parts-site',subdir)),
                os.path.abspath(os.path.join('.','.parts-site',subdir))
                #homedir/.parts-site
                ]+localpath+syspath+[
                # user part-site in parts install
                os.path.join(glb.parts_path,'parts-site',subdir),
                # parts install
                os.path.join(glb.parts_path,subdir)
            ]
        
        g_site_dir_cache[subdir]=sitepaths
    return g_site_dir_cache[subdir]

def load_module(path,name,type):
    """Return the imported module
    made more generic so Parts can reuse the logic
    instead of using the C&P anti-patttern.
    """
    
    modname='<'+type+'>'+name
    if not sys.modules.has_key(modname):
        api.output.verbose_msg("load_module",'Trying to load module <%s> type <%s>'%(name,type))
        file, path1, desc = imp.find_module(name,path)
        oldPath = sys.path[:]
        sys.path=path+sys.path
        
        try:
            mod = imp.load_module(modname, file, path1, desc)
            api.output.verbose_msg("load_module","Module was loaded from <%s>"%path1)
        except ImportError,e:
            ec_str=StringIO.StringIO()
            traceback.print_exc(file=ec_str)
            api.output.verbose_msg("load_module","Failed to load module!")
            api.output.verbose_msg(["load_module_failure","load_module"],"Stack:\n%s"%(ec_str.getvalue()))
            if file:
                file.close()
            raise SCons.Errors.UserError, "No module named '%s'" % (name)
        finally:
            sys.path = oldPath
        if file:
            file.close()
        
    return sys.modules[modname]
    
