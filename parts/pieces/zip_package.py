import parts.errors
import parts.common as common
import parts.glb as glb

from SCons.Debug import logInstanceCreation

def map_zip_builder(env, target, sources, stackframe, **kw):
    def zip_builder():
        new_sources, _ = env.Override(kw).GetFilesFromPackageGroups(target, sources, stackframe)

        # really call the builder so everything is setup correctly
        return env.ZipFile(target, new_sources, src_dir="$INSTALL_ROOT", **kw)
    return zip_builder

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

    glb.engine.add_preprocess_logic_queue(map_zip_builder(env, target[0], sources,
                parts.errors.GetPartStackFrameInfo(), **kw))
    return target


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

SConsEnvironment.ZipPackage=ZipPackage_wrapper






