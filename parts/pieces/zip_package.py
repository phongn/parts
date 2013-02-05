import parts.common as common
import parts.glb as glb

from SCons.Debug import logInstanceCreation

class map_zip_builder(object):
    def __init__(self,env,target,sources,**kw):
        if __debug__: logInstanceCreation(self)
        self.env=env
        self.target=target
        self.sources=sources
        self.kw=kw

    def __call__(self):
        new_sources=[]
        # turn the Part value in to a set of File objects
        for s in self.sources:
            common.extend_unique(new_sources,self.env.GetPackageGroupFiles(s))

        # really call the builder so everything is setup correctly
        ret=self.env.ZipFile(self.target,new_sources,src_dir="$INSTALL_ROOT")
        # really call the builder so everything is setup correctly
        return ret

def ZipPackage_wrapper(env,target,sources,**kw):
    # currently we assume all sources are Group values
    # will probally change this once we understand better

    target = common.make_list(target)
    sources= common.make_list(sources)

    if len(target) > 1:
        raise SCons.Errors.UserError('Only one target is allowed.')

    if str(target[0]).endswith('.zip'):
        target=[env.Dir(".").File(target[0])]
    else:
        target=[env.Dir(".").File(target[0]+".zip")]

    sources=[env.subst(s) for s in sources]

    glb.engine.add_preprocess_logic_queue(map_zip_builder(env,target[0],sources,**kw))
    return target


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.ZipPackage=ZipPackage_wrapper






