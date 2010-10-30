# this handle overrides to the env [] operators

from .. import common

def Parts__setitem__(self,key,val):
    if getattr(self,'_log_keys',False):
        if self.has_key(key)==False:
            pobj=common.g_engine._part_manager._from_env(self)
            if pobj and common.is_string(val):
                pobj._env_exports[key]=val
    self._orig__setitem__(key,val)
    if isinstance(val,common.bindable):
        try:
            self.bindable_vars.append(key)
        except:
            self.bindable_vars=[key]
        val._bind(self,key)

# not using get at the moment.. however that could change
def Parts__getitem__(self,key):
    
    tmp=self._orig__getitem__(key)
    if hasattr(tmp,'__eval__'):
        tmp=tmp.__eval__()
        self._orig__setitem__(key,tmp)
    return tmp



from SCons.Script.SConscript import SConsEnvironment

# override __setitem__ bind env with bindable objects when set
SConsEnvironment._orig__setitem__=SConsEnvironment.__setitem__
SConsEnvironment.__setitem__=Parts__setitem__

SConsEnvironment._orig__getitem__=SConsEnvironment.__getitem__
SConsEnvironment.__getitem__=Parts__getitem__
