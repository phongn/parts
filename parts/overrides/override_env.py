# this overide will overide the init function in the overide environment to auto add the SPAWN value
# this is done to allow the overide environment to be seen by the spawn object ( in case it us a 
# Part spawer object) so we can read the correct values from it

from .. import common

def _Parts__init__(self, subject, overrides={}):
    # check to see if the overides SPAWN value in it
    if 'SPAWN' not in overrides:
        # add a copy the spawn value given this is a Parts Spawn value
        spawn=subject.get('SPAWN')
        if isinstance(spawn,common.bindable):
            tmp={'SPAWN':spawn._rebind(self,"SPAWN")}
            tmp.update(overrides)
            overrides=tmp

    #call orginal __init__ function
    self._orig__init__(subject,overrides)

from SCons.Environment import OverrideEnvironment
# override __setitem__ bind env with bindable objects when set
OverrideEnvironment._orig__init__=OverrideEnvironment.__init__
OverrideEnvironment.__init__=_Parts__init__

