from Common.java import java
from SCons.Tool import javac
from SCons.Tool.JavaCommon import parse_java_file

# monkey patch emit_java_classes to do the Right Thing
# otherwise generated classes have no package name and get rebuilt always

_DEFAULT_JAVA_EMITTER = javac.emit_java_classes

def emit_java_classes(target, source, env):
    """
    Set correct path for .class files from generated java source files
    """
    classdir = target[0]
    tlist, slist = _DEFAULT_JAVA_EMITTER(target, source, env)
    if 'APP_PACKAGE' in env:
        out = []
        for entry in slist:
            classname = env['APP_PACKAGE'] + entry.name.replace('.java', '')
            java_file = source[0].File(os.path.join(
                    env['APP_PACKAGE'].replace('.', '/'), entry.name))
            if os.path.exists(java_file.abspath):
                version = env.get('JAVA_VERSION', '1.4')
                pkg_dir, classes = parse_java_file(
                                java_file.rfile().get_abspath(), version)
                for output in classes:
                    class_file = classdir.File(
                                os.path.join(pkg_dir, str(output) + '.class'))
                    class_file.attributes.java_classdir = classdir
                    class_file.attributes.java_sourcedir = entry.dir
                    class_file.attributes.java_classname = str(output)
                    out.append(class_file)
            else:
                class_file = classdir.File(os.path.join(
                        env['APP_PACKAGE'].replace('.', '/'),
                        entry.name.replace('.java', '.class')))
                class_file.attributes.java_classdir = classdir
                class_file.attributes.java_sourcedir = entry.dir
                class_file.attributes.java_classname = classname
                out.append(class_file)
        return out, slist
    else:
        return tlist, slist

javac.emit_java_classes = emit_java_classes

def generate(env, *args, **kw):

    java.MergeShellEnv(env)

    javac.generate(env, *args, **kw)

def exists(env):
    return javac.exists(env)

# vim: set et ts=4 sw=4 ai :

