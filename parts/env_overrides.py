## this file contains functions I overide in SCons for various reasons
## most of these are just function proxies to add internal like functionality
## where I need it. Hopefully most of these items will move into SCons in some form

import SCons.Script
import SCons.Util
import SCons.Environment
import os


class bindable(object):
    pass

def PartsClone(self, tools=[], toolpath=None, parse_flags = None, **kw):
    clone_env=self._orig_Clone(tools,toolpath,parse_flags,**kw)
    #rebind and bindable 
    clone_env.bindable_vars=[]
    if hasattr(self, 'bindable_vars'):
        for i in self.bindable_vars:
            clone_env.bindable_vars.append(i)
            clone_env[i]=clone_env[i]._rebind(clone_env,i)
    return clone_env
        

def Parts__setitem__(self,key,val):
    self._orig__setitem__(key,val)
    if isinstance(val,bindable):
        try:
            self.bindable_vars.append(key)
        except:
            self.bindable_vars=[key]
        val._bind(self,key)


class PartPathDirsWrapper:
    """This is a wrapper class to work around a "bug" with the scanner in that
    it tries to delay expand variables which might modify the Env. This
    allows use to expand the area in the env before it tries to create the tuple
    list of paths that it will use to scan with. """
    def __init__(self, obj):
        self.obj = obj
        #print "$$$",obj.variable
    def __call__(self, env, dir, target=None, source=None, argument=None):
        import mappers
        def_env=SCons.Script.DefaultEnvironment()
        prop_lst=env.get(self.obj.variable,[])
        if prop_lst!=[]:
            ret=mappers.sub_lst(env,prop_lst,def_env)
            env[self.obj.variable]=ret
        #print 'Scanner', target[0]        
        return self.obj(env,dir,target,source,argument)


def Scanner_override():
    ## this is for fixing an issue with the scanners in which one item in a env
    ## does not have the $vars fully expanded, which causes an issue with in the
    ## dependency tree. This leads to a false rebuild of few files
    for k in SCons.Tool.SourceFileScanner.function.keys():
        if isinstance(SCons.Tool.SourceFileScanner.function[k].path_function,SCons.Scanner.FindPathDirs):
            SCons.Tool.SourceFileScanner.function[k].path_function=PartPathDirsWrapper(
            SCons.Tool.SourceFileScanner.function[k].path_function)

cc=[]
cct=[]

Orig_BuildWrapper=SCons.Environment.BuilderWrapper
class Parts_BuilderWrapper(Orig_BuildWrapper):

    def __call__(self, target=None, source=SCons.Environment._null, *args, **kw):
        
        # get default env
        def_env=SCons.Script.DefaultEnvironment()
        # get current part info
        alias=def_env.get('DEFINING_PART')
        

        dup=kw.get("allow_duplicates",False)
        found=False
        if dup:
            #Get info for help store info matches better
            if alias is not None:
                pinfo=def_env['PART_INFO'][alias]
                name=pinfo.get('NAME')
                srcpath=pinfo['ENV']['SRC_DIR']
            else:
                name=None
                srcpath=None
            # make key
            if SCons.Util.is_String(source):
                s=os.path.split(str(source))[1]
            else:
                s=os.path.split(str(source[0]))[1]
            
            if target == []:
                key=(srcpath,s,self.name,name)
            else:
                key=(target,s,self.name,name)
            #print key
            #test for match
            if key in cc:
                #print "seen this one!!!!!!!!!!!!!!!!!!!",cc.index(key)
                #print key
                tmp= cct[cc.index(key)]
                found=True
                
        if not found:
            tmp=Orig_BuildWrapper.__call__(self,target, source, *args, **kw)
        
        #take care of resolved target information.
        if dup:
            cc.append(key)
            cct.append(tmp)
        if alias is not None:
            pinfo=def_env['PART_INFO'][alias]
            pinfo['TARGET_FILES'].extend(tmp)
        return tmp


def my_semi_deepcopy(x):
    copier = SCons.Util._semi_deepcopy_dispatch.get(type(x))
    if copier:
        return copier(x)
    else:
        return SCons.Util._semi_deepcopy_inst(x)

SCons.Util.semi_deepcopy=my_semi_deepcopy

from SCons.Script.SConscript import SConsEnvironment

# override Clone to deepcopy bindable objects
SConsEnvironment._orig_Clone=SConsEnvironment.Clone
SConsEnvironment.Clone=PartsClone

# override __setitem__ bind env with bindable objects when set
SConsEnvironment._orig__setitem__=SConsEnvironment.__setitem__
SConsEnvironment.__setitem__=Parts__setitem__

# override the builder wrapper to allow us to get the files defined in the scope of a part
SCons.Environment.BuilderWrapper=Parts_BuilderWrapper