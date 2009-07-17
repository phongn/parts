## this file contains functions I overide in SCons for various reasons
## most of these are just function proxies to add internal like functionality
## where I need it. Hopefully most of these items will move into SCons in some form

import SCons.Script
import SCons.Util

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