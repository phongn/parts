import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil, os
import tempfile

def rpm_spec(env,target,source,**kw):

    target_name= env.subst('$NAME')
    target_version= env.subst('$VERSION')
    target_release= env.subst('$RELEASE')
    target_arch= env.subst('$TARGET_ARCH')

    #path to the specfile
    bd=env.Dir(env.subst('${{BUILD_DIR}}/SPECS/{0}'.format(target[0].name[:-4]))).abspath

    spec_dict = {}
    #Use function read_spec to build dictionary from the spec file
    # override the information if there is no match with the target provided
    def rpmspec():
        lis = os.listdir(bd) # list of specfiles in the build dir/SPECS
        for filen in lis:
            filep = os.path.join(bd, filen)
            file_obj = open(filep, 'r')
            file_content = file_obj.read()
            file_obj.close()

        #If BuildArch exists in specfile, delete the line
        # It will take host architecture as the build architecture by default

        fobjw = open(filep, 'wb')
        for item in file_content.split('\n'):
            if not item.startswith('BuildArch'):
                 fobjw.write('{0}\n'.format(item))
            else:
                pass
        fobjw.close()

        file_obj = open(filep, 'r')
        file_content = file_obj.read()
        file_obj.close()

        for item in file_content.split('\n'):
            token = item.replace(" ","").split(':')
            spec_dict[token[0]] = token[1:]

        keyset = ['Name','Version','Release']
        #Check if the dict has keys "Name","Version","Release". If doesn't exist print a "value missing" message

        for key in keyset:
            if spec_dict.has_key(key):
                filename_spec = spec_dict['Name'][0]+'-'+spec_dict['Version'][0]+'-'+spec_dict['Release'][0]
            else:
                print "Entries (Name or Version or Release) is missing from the specfile"

        filename_target = target_name+'-'+target_version+'-'+target_release

        #Check if the filename from specfile matches with the filename (target) from parts file
        # If a match continue
        # Else override the values of the specfile

        if filename_spec == filename_target and not spec_dict.has_key('BuildArch'):
            pass
        else:
            print "Overriding the spec file values for name, version, release"
            fobj = open(filep, 'wb')
            for line in file_content.split('\n'):
                if not line.startswith(('Name','Version','Release')):
                    fobj.write('{0}\n'.format(line))
                if line.startswith('Name'):
                    name = line.replace(line,('Name:'+target_name))
                    fobj.write('{0}\n'.format(name))
                if line.startswith('Version'):
                    version = line.replace(line,('Version:'+target_version))
                    fobj.write('{0}\n'.format(version))
                if line.startswith('Release'):
                    release = line.replace(line,('Release:'+target_release))
                    fobj.write('{0}\n'.format(release))
            fobj.close

        return spec_dict

    rpmspec()

    #filename to used to build the tar.gz file
    filename = target_name+'-'+target_version

    #############################################
    ##create the source gz file
    #Replace source with the name and version  from the specfile for proper formatting of build of the tar.gz file
    #and building the rpm

    ret = env.CCopyAs(
                [('${{BUILD_DIR}}/'+filename+'/{0}').format(env.Dir('${INSTALL_ROOT}').rel_path(n)) for n in source ],
                source,
                CCOPY_LOGIC='hard-copy'
               )

    env.TarGzFile((('${{BUILD_DIR}}/_rpm/{0}/SOURCES/{1}.tar.gz').format(target[0].name[:-4],filename)),ret)
    env.CCopyAs(env.Dir('${{BUILD_DIR}}/_rpm/{0}/SPECS'.format(target[0].name[:-4])),env.Dir('${{BUILD_DIR}}/SPECS/{0}'.format(target[0].name[:-4])))
    env._rpm('${{BUILD_DIR}}/_rpm/{0}'.format(target[0].name[:-4]))

rpmspec_action = SCons.Action.Action(rpm_spec)

api.register.add_builder('_rpmspec',SCons.Builder.Builder(
                    action = rpmspec_action,
                    source_factory = SCons.Node.FS.Entry,
                    target_factory = SCons.Node.FS.File
                    ))