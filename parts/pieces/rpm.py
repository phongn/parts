import SCons.Script
import parts.api as api

rpm_action = SCons.Action.Action([
        'mkdir -p ${SOURCE}/BUILD',
        ('rpmbuild  --define "_topdir ${SOURCE.abspath}" '
         '--define "_rpmdir ${SOURCE.abspath}" '
         '--define "_build_name_fmt %%{Name}-%%{Version}-%%{Release}.%%{Arch}.rpm" -bb '
         '--target=${TARGET_ARCH} --quiet ${SOURCE}/SPECS/*')])

# internal rpm package builder... meant to be called by RPMPackage function internally
api.register.add_builder('_rpm',SCons.Builder.Builder(
                    action = rpm_action,
                    source_factory = SCons.Node.FS.Entry,
                    target_factory = SCons.Node.FS.File,
                    suffix = '.rpm',
                    single_source=True)
                    )