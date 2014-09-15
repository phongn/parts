import SCons.Script
import parts.api as api
import parts.errors
import parts.common as common
import parts.glb as glb
import shutil, os
import tempfile


def is_macro_header(line):
    if line.startswith('%description'):
        return True
    if line.startswith('%prep'):
        return True
    if line.startswith('%check'):
        return True
    if line.startswith('%build'):
        return True
    if line.startswith('%install'):
        return True
    if line.startswith('%clean'):
        return True
    if line.startswith('%files'):
        return True
    return False


def add_install_content(file_contents, idx=-1):
    lines = ['rm -rf %{buildroot}', 'mkdir -p  %{buildroot}',
             'cp -a * %{buildroot}']

    if idx == -1:
        file_contents.append('%install')
        for i in xrange(len(lines)):
            file_contents.append(lines[i])
    else:
        for i in xrange(len(lines)):
            file_contents.insert(idx+1+i, lines[i])


def add_files_content(env, file_contents, pkg_files_objs, idx=-1):
    # add all content in archive file
    defattrs = '%defattr(-,root,root,-)'


    f2 = env.subst('${BUILD_DIR}')
    f3 = env.subst('${INSTALL_ROOT}')

    files = []
    for f in pkg_files_objs:
        #print ("***PKG FILE " + str(f))
        files.append(f.ID.replace(env.subst('${INSTALL_ROOT}'),
                                    '%_prefix/../'))
        #print ("***PKG FILE2 " + str(files[-1]))

	#TODO add like of MetaTag attributes mapping to RPM
    if idx == -1:
        file_contents.append('%files')
        file_contents.append(defattrs)
        for i in xrange(len(files)):
            file_contents.append(files[i])
    else:
        file_contents.insert(idx+1+i, defattrs)
        for i in xrange(len(files)):
            file_contents.insert(idx+2+i, files[i])

def rpm_spec(env, target, source):

    # these are set from rpm_package wrapper function
    target_name= env['NAME']
    target_version= env['VERSION']
    target_release= env['RELEASE']
    pkg_files = env['PKG_FILES']

    # open spec file
    with open(source[0].abspath, 'r') as file_obj:
        file_contents = file_obj.read().split('\n')

    # If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents = filter(lambda x : not x.startswith('BuildArch') ,
                           file_contents)

    # override some value to match name of out rpm files.
    found_install = False
    found_files = False

    print "Overriding the spec file values for name, version, release"
    i=0
    #tmp set to detect duplicates of values that should only be defined once
    tmp=set(('name', 'version', 'release'))

    while i < len(file_contents): 

        if file_contents[i].startswith('Name'):
            file_contents[i]='Name:'+target_name
            try:
                tmp.remove('name')
            except KeyError:
               pass

        elif file_contents[i].startswith('Version'):
            file_contents[i] = 'Version:'+target_version            
            try:
                tmp.remove('version')
            except KeyError:
               pass

        elif file_contents[i].startswith('Release'):
            file_contents[i] = 'Release:'+target_release
            try:
                tmp.remove('release')
            except KeyError:
               pass

        #check for %install section where files are added to buildroot staging 
        #area, the staging area gets contents from the source.tar.gz file
        elif file_contents[i].startswith('%install'):
            found_install = True

            #remove existing install section
            j = i+1
            while not is_macro_header(file_contents[j]):
                file_contents.pop(j)

            # add the content
            add_install_content(file_contents, i)

        #add file contents that will be installed in rpm
        elif file_contents[i].startswith('%files'):
            found_files = True   
            add_files_content(env, file_contents, pkg_files, i)
         
        i+=1

    #add sections if they do not exist
    if not found_install:
        add_install_content(file_contents)

    if not found_files:
        add_files_content(env, file_contents, pkg_files)
        

    if tmp:
        api.output.warning_msg("Did not find keys value in spec file for {0}".format(", ".join(tmp)))
        
    #If BuildArch exists in specfile, delete the line
    # It will take host architecture as the build architecture by default
    file_contents= "\n".join(file_contents)+'\n'
    with open(target[0].abspath, 'wb') as out_file:
        out_file.write(file_contents)

    
rpmspec_action = SCons.Action.Action(rpm_spec)

api.register.add_builder('_rpmspec',SCons.Builder.Builder(
                    action = rpmspec_action,
                    source_factory = SCons.Node.FS.File,
                    target_factory = SCons.Node.FS.File
                    ))
