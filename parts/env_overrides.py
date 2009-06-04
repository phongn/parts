## this file contains functions I overide in SCons for various reasons
## most of these are just function proxies to add internal like functionality
## where I need it. Hopefully most of these items will move into SCons in some form

import SCons.Script

class bindable(object):
    pass

def PartsClone(self, tools=[], toolpath=None, parse_flags = None, **kw):
    clone_env=SCons.Script.Environment._orig_Clone(self,tools,toolpath,parse_flags,**kw)
    #rebind and bindable 
    clone_env.bindable_vars=[]
    if hasattr(self, 'bindable_vars'):
        for i in self.bindable_vars:
            clone_env.bindable_vars.append(i)
            clone_env[i]=clone_env[i].rebind(clone_env)
    return clone_env
        

def Parts__setitem__(self,key,val):
    SCons.Script.Environment._orig__setitem__(self,key,val)
    if isinstance(val,bindable):
        try:
            self.bindable_vars.append(key)
        except:
            self.bindable_vars=[key]
        val.bind(self)


from SCons.Script.SConscript import SConsEnvironment

# override Clone to deepcopy bindable objects
SConsEnvironment._orig_Clone=SConsEnvironment.Clone
SConsEnvironment.Clone=PartsClone

# override __setitem__ bind env with bindable objects when set
SConsEnvironment._orig__setitem__=SConsEnvironment.__setitem__
SConsEnvironment.__setitem__=Parts__setitem__