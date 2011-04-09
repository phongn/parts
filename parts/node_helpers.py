''' 
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''

import glb
import common
import api.output
import metatag

import SCons.Script

import os


class ninfotmp(object):
    def __init__(self):
        self.timestamp=0
        self.csig=0 

def node_up_to_date(node):
    ''' 
    Expects a Scons node objects, will test aginst stored info 
    to see if it is uptodate
    '''
    
    if isinstance(node,SCons.Node.Node):
        node.disambiguate()
        dbentry=node.get_stored_info()
        ninfo=dbentry.ninfo
        
    elif common.is_string(node):
        node=glb.engine.def_env.Entry(node)
        node.disambiguate()
        tmp=metatag.MetaTagValue(node,'uptodate','parts',None)
        if tmp is True:
            return True
        elif tmp is None:
            pass
        else:
            api.output.verbose_msg("update_check",tmp)
            return False
        dbentry=node.get_stored_info()
        ninfo=dbentry.ninfo
        
    else:
        node=glb.engine.def_env.Entry(node['name'])
        node.disambiguate()
        tmp=metatag.MetaTagValue(node,'uptodate','parts',None)
        if tmp is True:
            return True
        elif tmp is None:
            pass
        else:
            api.output.verbose_msg("update_check",tmp)
            return False
        
        ninfo=ninfotmp()
        ninfo.timestamp=node.get('timestamp')
        ninfo.csig=node.get('csig')
        
        
    # see if node time stamp matches
    tmp=getattr(ninfo,'timestamp',None)
    if tmp is None:
        s="'%s' does not exist in the SCons DB"%(node)
        metatag.MetaTag(node,ns='parts',uptodate=s)
        api.output.verbose_msg("update_check",s)
        return False
    if node.exists() == False:
        s="'%s' does not exist"%(node)
        metatag.MetaTag(node,ns='parts',uptodate=s)
        api.output.verbose_msg("update_check",s)
        return False
    if node.get_timestamp() != tmp:
        # timestamp did not match.. try md5
        api.output.verbose_msg("update_check","TimeStamp diff in '%s'"%(node))
        if node.get_csig() != getattr(ninfo,'csig',0):
            # md5 failure
            #print ninfo.__dict__,node.get_csig()
            s="%s is out of date because of differences"%(node)
            metatag.MetaTag(node,ns='parts',uptodate=s)
            api.output.verbose_msg("update_check",s)
            return False
    #api.output.verbose_msg("update_check","%s seems to be unmodified"%(node))
    metatag.MetaTag(node,ns='parts',uptodate=True)
    return True


class _AbsFile(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,path):
        return self.env.File(str(path),self.env['SRC_DIR']).srcnode().abspath

class _AbsDir(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,path):
        return self.env.Dir(str(path),self.env['SRC_DIR']).srcnode().abspath

def AbsFile(env,path):
    tmp=env.File(str(path),env['SRC_DIR'])
    common.tag_node_ownership(env,tmp.Dir('.'))
    return tmp.srcnode().abspath

def AbsDir(env,path):
    tmp = env.Dir(str(path),env['SRC_DIR'])
    common.tag_node_ownership(env,tmp)
    return tmp.srcnode().abspath
    
    
def SymLinkEnv(env,name,linkto):#,*args,**kw):
    #tmp=env.File(name,*args,**kw)
    #env.MetaTag(tmp,SymLink=linkto)
    #return tmp
    tmp=env.__make_link__(target=name,linkto=linkto)
    if len(tmp) > 1:
        raise SCons.Errors.UserError("Symlink can only have one Target")
    return tmp[0]

def make_link_Emit(target, source, env):
    tmp=target[0]
    if env['HOST_OS']=='win32' and (
        tmp.path.endswith('.lnk')==False and tmp.path.endswith('.url')==False):
            tmp=env.File(str(tmp)+'.lnk')
    env.MetaTag(tmp,SymLink=env.get('linkto',''))
    return ([tmp],[])

def make_link_bf(target, source, env):
    t=target[0]
    symlink=env.MetaTagValue(t,'SymLink')
    make_dummy_file=env.MetaTagValue(t,'SymLinkMakeDummyFile',default=True)
    print "Creating SymLink",t.get_path(),"pointing to",symlink
    if env['HOST_OS']=='win32':
        import win32file
        import win32com.client
        if symlink is not None:
            # make a short cut for now on windows
            # deal later with vista ability to make a symlink
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(t.get_path()+'.lnk')
            shortcut.Targetpath = os.path.normpath(os.path.join(os.path.abspath(os.path.split(t.get_path())[0]),symlink))
            shortcut.save()
    else:
        if os.path.lexists(t.get_path()):
            try:
                val=os.readlink(t.get_path())
                if val!=symlink:
                    os.unlink(t.get_path())
                    os.symlink(symlink,t.get_path())
            except:
                os.unlink(t.get_path())
                os.symlink(symlink,t.get_path())
        else:
            os.symlink(symlink,t.get_path())
        if make_dummy_file:
            #hack to get around the use of exist vs lexists in SCons
            if symlink[0]=='/': # absdir
                if os.path.lexists(symlink)==False:
                    try:
                        f=open(symlink,'w')
                        f.write(symlink)
                    except:
                        pass
            else: # non absdir link            
                symfile=os.path.abspath(os.path.join(os.path.split(t.get_path())[0],symlink))
                if os.path.lexists(symfile)==False:
                    try:
                        f=open(symfile,'w')
                        f.write(symlink)
                    except:
                        pass
        
    return None


api.register.add_builder('__make_link__',SCons.Builder.Builder(
        action         = SCons.Action.Action(make_link_bf),
        target_factory = SCons.Node.FS.File,
        source_factory = SCons.Node.FS.Entry,
        emitter        = make_link_Emit
        ))

# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

#add as global to part scope
api.register.add_global_parts_object('AbsFile',_AbsFile,True)
api.register.add_global_parts_object('AbsDir',_AbsDir,True)

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile=AbsFile
SConsEnvironment.AbsDir=AbsDir

SConsEnvironment.SymLink=SymLinkEnv
