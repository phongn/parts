from Common.java import java
from SCons.Tool import javac

def generate(env, *args, **kw):

    java.MergeShellEnv(env)

    javac.generate(env, *args, **kw)

def exists(env):
    return javac.exists(env)

# vim: set et ts=4 sw=4 ai :

