
import zipfile
import os
import SCons.Script
import parts.common as common


def zip(target, source, env):
        zf = zipfile.ZipFile(str(target[0]), 'w',zipfile.ZIP_DEFLATED)
        for s in source:
            tmp=s.path
            root_dir=env.get('src_dir',None)
            if root_dir is not None:
                root_dir=env.Dir(env.subst(root_dir)).path
                t=tmp[len(root_dir):]
                zf.write(tmp,t)
            else:
                bd=env.Dir(env.subst('$BUILD_DIR')).path
                sd=env.Dir(env.subst('$SRC_DIR')).path
                if tmp.startswith(bd):
                    t=tmp[len(bd):]
                    zf.write(tmp,t)
                elif tmp.startswith(sd):
                    t=tmp[len(sd):]
                    zf.write(tmp,t)
                else:
                    zf.write(tmp)
        zf.close()


ZipAction = SCons.Action.Action(zip)

common.AddBuilder('ZipFile',SCons.Builder.Builder(action = ZipAction,
                                   source_factory = SCons.Node.FS.Entry,
                                   source_scanner = SCons.Defaults.DirScanner,
                                   suffix = '.zip'))#,multi = 1))