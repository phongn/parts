import SCons.Script
import parts.api as api

rpm_action = SCons.Action.Action([
        'mkdir -p ${TARGET.dir}/BUILD',
        ('rpmbuild  --define "_topdir ${TARGET.Dir(\".\").abspath}" '
         '--define "_rpmdir ${TARGET.Dir(\".\").abspath}" '
         '-bb '
         '--target=${TARGET_ARCH} --quiet ${TARGET.dir}/SPECS/*')])

# internal rpm package builder... meant to be called by RPMPackage function internally
api.register.add_builder('_rpm',SCons.Builder.Builder(
                    action = rpm_action,
                    source_factory = SCons.Node.FS.Entry,
                    target_factory = SCons.Node.FS.File,
                    suffix = '.rpm')
                    )
