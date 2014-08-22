import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil, os
import tempfile

def rpm_spec(env,target,source):

    # these are set from rpm_package wrapper function
    target_name= env['NAME']
    target_version= env['VERSION']
    target_release= env['RELEASE']

    # open spec file
    with open(source[0].abspath, 'r') as file_obj:
        file_contents = file_obj.read().split('\n')

    # If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents = filter(lambda x : not x.startswith('BuildArch') ,file_contents)

    # override some value to match name of out rpm files.
    print "Overriding the spec file values for name, version, release"
    i=0
    tmp=set(('name', 'version', 'release'))
    for line in file_contents: 
        if line.startswith('Name'):
            file_contents[i]='Name:'+target_name
            # should only hit it once... but to be safe..
            try:
                tmp.remove('name')
            except KeyError:
               pass
        elif line.startswith('Version'):
            file_contents[i] = 'Version:'+target_version            
            # should only hit it once... but to be safe..
            try:
                tmp.remove('version')
            except KeyError:
               pass
        elif line.startswith('Release'):
            file_contents[i] = 'Release:'+target_release
            # should only hit it once... but to be safe..
            try:
                tmp.remove('release')
            except KeyError:
               pass
        i+=1
    if tmp:
        api.output.warning_msg("Did not find keys value in spec file for {0}".format(", ".join(tmp)))
        
    #If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents= "\n".join(file_contents)
    with open(target[0].abspath, 'wb') as out_file:
        out_file.write(file_contents)

    
rpmspec_action = SCons.Action.Action(rpm_spec)

api.register.add_builder('_rpmspec',SCons.Builder.Builder(
                    action = rpmspec_action,
                    source_factory = SCons.Node.FS.File,
                    target_factory = SCons.Node.FS.File
                    ))
