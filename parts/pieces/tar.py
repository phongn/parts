import os,tarfile
import SCons.Script
import parts.common as common

def tar(target, source, env):
        zf = tarfile.open(str(target[0]), 'w')
        for s in source:
            tmp=s.path
            root_dir=env.get('src_dir',None)
            if root_dir is not None:
                root_dir=env.Dir(env.subst(root_dir)).path
                t=tmp[len(root_dir):]
                zf.add(tmp,t)
            else:
                bd=env.Dir(env.subst('$BUILD_DIR')).path
                sd=env.Dir(env.subst('$SRC_DIR')).path
                if tmp.startswith(bd):
                    t=tmp[len(bd):]
                    zf.add(tmp,t)
                elif tmp.startswith(sd):
                    t=tmp[len(sd):]
                    zf.add(tmp,t)
                else:
                    zf.add(tmp)
        zf.close()
    
        #tar=tarfile.open(source,'r')
        #tar.extractall(destination)
        #tar.close()

TarAction = SCons.Action.Action(tar)
common.AddBuilder('LibPackage',SCons.Builder.Builder(action = TarAction,
                                   source_factory = SCons.Node.FS.Entry,
                                   source_scanner = SCons.Defaults.DirScanner,
                                   suffix = '.so-gz'))#,multi = 1))

common.AddBuilder('TarFile',SCons.Builder.Builder(action = TarAction,
                                   source_factory = SCons.Node.FS.Entry,
                                   source_scanner = SCons.Defaults.DirScanner,
                                   suffix = '.gz'))#,multi = 1))