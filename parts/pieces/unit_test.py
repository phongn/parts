
import parts.glb as glb
import parts.common as common
import parts.api as api
import parts.errors as errors
import parts.node_helpers as node_helpers
import parts.pattern as pattern
import parts.functors as functors
import parts.parts as parts
import parts.api.output as output
import parts.pnode as pnode

import SCons.Script

import os,stat,sys
import string


#map unit testing stuff.. clean up depends..

###########################################
## unit test script file writer
###########################################
def unit_test_script_bf_str(target = None, source = None, env = None):
    return "PARTS: Writing unit test launch scripts"

def unit_test_script_bfe(target, source, env):
    # get target file
    tf=os.path.split(str(target[0]))[1]
    # make new name
    target+=[
        target[0].Dir('.').File(tf+'.cmd')
        ]
    #env.Clean(env['ALIAS'],tout)
    return (target,source)

def unit_test_script_bf(target, source, env):
    f = open(str(target[0]), 'wb')

    cmd=env.subst("$UNIT_TEST_RUN_COMMAND")
    command_env=env.get('UNIT_TEST_ENV',{})

    # update the value
    for k,v in command_env.iteritems():
        command_env[k]=env.subst(v)

    command='''#! /usr/bin/env python
import os,sys
import string
import subprocess

curr_path=os.path.split(os.path.abspath(sys.argv[0]))[0]
os.chdir(curr_path)
env=os.environ
env.update('''+str(command_env)+''')
env['UNIT_TEST_DIR']=curr_path
cmd=r"'''+cmd+'''"
if len(sys.argv) > 1:
    cmd = cmd+" "+' '.join(sys.argv[1:])
else:
    cmd=cmd
print cmd
proc = subprocess.Popen (cmd, env=env, shell=True)
proc.wait()
sys.stdout.flush()
sys.stderr.flush()
sys.exit(proc.returncode)

'''
    f.write(command)
    f = open(str(target[1]), 'wb')
    f.write("@pushd %~dp0\r\n@python "+target[0].name+" %*\r\nset ERROR_LEVEL=%ERRORLEVEL%\r\n@popd\r\nexit %ERROR_LEVEL%")
    f.close()
    st = os.stat(str(target[0]))
    os.chmod(str(target[0]), stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)
    st = os.stat(str(target[1]))
    os.chmod(str(target[1]), stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)



from parts.target_type import target_type
def unit_test(env,target,source,command_args=[],data_src=[],src_dir='.',make_pdb=True,depends=None,builder="Program",builder_kw={},**kw):

    #to help with user errors
    errors.SetPartStackFrameInfo()

    if ("utest::" in env["SUPPRESS_SECTION"] or
        "utest" in env["SUPPRESS_SECTION"]) and \
        SCons.Script.GetOption('section_suppression'):
        api.output.verbose_msgf("warning",'Skipping the processing of Part section "utest" in Part {0}',env.PartName())
        return []
    skip_run_test=False
    if ("run_utest::" in env["SUPPRESS_SECTION"] or
        "run_utest" in env["SUPPRESS_SECTION"]) and \
        SCons.Script.GetOption('section_suppression') or (env['HOST_OS'] <> env['TARGET_OS']):
        api.output.verbose_msgf("warning",'Skipping the processing of Part section "run_utest" of section "utest" in Part {0}',env.PartName())
        skip_run_test=True


    targets=SCons.Script.BUILD_TARGETS
    for t in targets:
        tmp=target_type(t)
        sep_len=len(env.subst("$ALIAS_SEPARATOR"))
        if tmp.Section == 'utest':
            break
    else:
        return []

    ## get Part object of Part defining the utest call
    parent_obj=glb.engine._part_manager._from_env(env)
    #Create a section object ( should get existing section if it already exists
    sec=glb.pnodes.Create(pnode.section.utest_section,parent_obj,env=env.Clone(**kw))
    # add section to Part container
    parent_obj._AddSection("utest",sec)
    # Set the "current defining section" to the utest section
    # and save current sectiond to be reset at end of function
    curr_sec=parent_obj.DefiningSection
    try:
        parent_obj.DefiningSection=sec

        # tweak Environment
        sec.Env['UNIT_TEST_TARGET']=target

         ## setup the varible with paths
        curr_path=env.AbsDir('.')
        rel_src_dir=common.relpath(env.AbsDir(src_dir),curr_path)
        if src_dir!='.':
            src_dir=common.relpath(env.Dir(os.path.join(curr_path,src_dir)).srcnode().abspath,env.Dir('.').abspath)
        else:
            src_dir=curr_path

        build_dir_leaf=sec.Env['UNIT_TEST_TARGET']
        build_dir=sec.Env.subst("{0}/{1}".format('$BUILD_DIR',build_dir_leaf))
        orig_build_dir=env.Dir('$BUILD_DIR').path
        build_dir_node=sec.Env.Dir(build_dir)
        ## change the build dir
        sec.Env.VariantDir(variant_dir=build_dir,src_dir=src_dir,duplicate=env['duplicate_build'])
        build_dir_node=sec.Env.Dir(build_dir)
        ## map autodepends stuff
        if depends is None:
            sec.Env.DependsOn([sec.Env.Component(env.PartName(),env.PartVersion(),section='build')])
        else:
            sec.Env.DependsOn(depends)

        ## flatten the sources
        source=sec.Env.Flatten(source)

        ## process the sources
        # we have to re-path value to map to the new variant directory
        src_files=[]
        for f in source:
            if isinstance(f,pattern.Pattern):
                flst=f.files()
                for i in flst:
                    if i.startswith(rel_src_dir):
                        i=i[len(rel_src_dir)+1:]
                    elif i.startswith(curr_path):
                        i=i[len(curr_path)+1:]
                    elif i.startswith(orig_build_dir):
                        i=i[len(orig_build_dir)+1:]
                    src_files.append(build_dir_node.File(i))

            elif isinstance(f,SCons.Node.FS.Dir):
                pass
            elif isinstance(f,SCons.Node.FS.File):
                # File node will start with the orginal build directory
                # or the start with current path ( ie full path to src)
                # or it might be equal to some messed up value based on the build directory
                # caused by the mix of ../ paths
                relpath=common.relpath(f.dir.ID,orig_build_dir)
                if f.path.startswith(curr_path):
                    f=f.path[len(curr_path)+1:]
                elif f.path.startswith(orig_build_dir):
                    fs=f.path[len(orig_build_dir)+1:]
                    if src_dir==curr_path:
                        src_files.append(f)
                    else:
                        src_files.append(build_dir_node.File(fs))
                elif f.ID.startswith(f.Dir(relpath).ID):
                    fs=f.ID[len(f.Dir(relpath).ID)+1:]
                    src_files.append(build_dir_node.File(fs))
            elif isinstance(f,SCons.Node.FS.Entry):
                # Entry (like File) node will start with the orginal build directory
                # or the start with current path ( ie full path to src)
                # or it might be equal to some messed up value based on the build directory
                # caused by the mix of ../ paths
                relpath=common.relpath(f.dir.ID,orig_build_dir)
                if f.path.startswith(curr_path):
                    f=f.path[len(curr_path)+1:]
                elif f.path.startswith(orig_build_dir):
                    fs=f.path[len(orig_build_dir)+1:]
                    if src_dir==curr_path:
                        src_files.append(f)
                    else:
                        src_files.append(build_dir_node.Entry(fs))
                elif f.ID.startswith(f.Dir(relpath).ID):
                    fs=f.ID[len(f.Dir(relpath).ID)+1:]
                    src_files.append(build_dir_node.Entry(fs))

            elif common.is_string(f):
                # normalize the path so we get matches on windows and posix based systems
                f=os.path.normpath(f)
                if f.startswith(rel_src_dir):
                    f=f[len(rel_src_dir)+1:]
                elif f.startswith(curr_path):
                    f=f[len(curr_path)+1:]
                src_files.append(build_dir_node.File(f))
            else:
                api.output.warning_msg("Unknown type in unit_test() in unit_test.py in Part",env.subst('$PART_NAME'))

        ## flatten the sources
        data_src=sec.Env.Flatten(data_src)

        ## process any data files
        out=[]
        dest_dir="$UNIT_TEST_DIR"
        for s in data_src:
            if isinstance(s,pattern.Pattern):
                t,sr=s.target_source(dest_dir)
                out+=sec.Env.CCopyAs(target=t,source=sr)
                #print "Pattern type"
            elif isinstance(s,SCons.Node.FS.Dir):
                #get all file in the directory
                #... add code...
                out+=sec.Env.CCopy(target=dest_dir,source=s)
                #print "Dir type"
            elif isinstance(s,SCons.Node.FS.File):
                out+=sec.Env.CCopy(target=dest_dir,source=s)
                #print "File type"
            elif isinstance(s,SCons.Node.Node):
                out+=sec.Env.CCopy(target=dest_dir,source=s)
            elif common.is_string(s):
                f=env.subst(s)
                if f.startswith(rel_src_dir):
                    f=f[len(rel_src_dir)+1:]
                elif f.startswith(curr_path):
                    f=f[len(curr_path)+1:]
                f=build_dir_node.File(f)
                out+=sec.Env.CCopy(target=dest_dir,source=f)
            else:
                api.output.warning_msg("Unknown type in unit_test() in unit_test.py in Part",env.subst('$PART_NAME'))

        ## the current path
        sec.Env.Append(CPPPATH= [src_dir])

        ## the option to build with PDB or not
        # might not to do this any more... as the PDB will work correctly on non windows systems
        if make_pdb==True:
            sec.Env['PDB']=build_dir+"/"+sec.Env['UNIT_TEST_TARGET_NAME']+'.pdb'
        else:
            sec.Env['PDB']=None

        ## the unit test we want to build
        tmp_bld=getattr(sec.Env,builder)
        if tmp_bld is None:
            api.output.error_msg("Builder {0} is not found".format(builder))
        ret = tmp_bld(target=build_dir+"/"+sec.Env['UNIT_TEST_TARGET_NAME'],source=src_files)
        #common.tag_node_ownership(pobj.Env,pobj.Env.Dir(build_dir))

        #build alias
        build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}'
        a=sec.Env.Alias(build_alias)

        tmp=[]
        for i in ret:
            if isinstance(i,SCons.Node.FS.File)or isinstance(i,SCons.Node.Node) or common.is_string(i):
                if common.is_catagory_file(sec.Env,'INSTALL_LIB_PATTERN',i):
                    tmp+=sec.Env.CCopy(target='$INSTALL_LIB',source=i)
                else:#if common.is_catagory_file(env,'SDK_BIN_PATTERN',i):
                    tmp+=sec.Env.CCopy(target='$INSTALL_BIN',source=i)
        ret = tmp

        ##make command args string
        if command_args:
            sec.Env['UTEST_CMDARGS']=command_args

        ## this builder makes the scripts to run the test on
        ## the command line with ease
        for k,v in sec.Env.get('UNIT_TEST_ENV',{}).iteritems():
            sec.Env['ENV'][k] = sec.Env.subst(v)
        #in case a python script is being called.. it is the same version of python as we are using
        sec.Env.PrependENVPath('PATH',os.path.split(sys.executable)[0],delete_existing=True)
        scripts_out=sec.Env.__UTEST__(build_dir+"/_scripts_/"+sec.Env['UNIT_TEST_SCRIPT_NAME'],[ret[0].abspath,sec.Env.Value(command_args),sec.Env.Value(sec.Env.subst("$UNIT_TEST_RUN_COMMAND"))],UNIT_TEST_ENV=sec.Env.get('UNIT_TEST_ENV',{}))
        scripts_out=sec.Env.CCopy("$UNIT_TEST_DIR",scripts_out)
        ### here we map a bunch of aliases
        core_alias=sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}',a+scripts_out+out+ret)
        # map top level run alias... first one maps to build based 'base_alias'
        if not skip_run_test:
            def wrap_exit_code_function(function, env, stackframe):
                '''
                SCons.Action object accepts exitstatfunc argument to be a callable
                with returncode as its only parameter. We want to pass some more arguments
                to our function.
                '''
                return lambda rcode: function(rcode, env=env, stackframe=stackframe)

            core_run_alias_env = sec.Env.Override(
                    dict(
                        TIME_OUT=sec.Env.get("RUN_UTEST_TIME_OUT",sec.Env.get('TIME_OUT')),
                        LOG_PART_FILE_NAME='run_utest.{0}.log'.format(ret[0].name)
                    )
                )
            core_run_alias=core_run_alias_env.Alias(
                    '${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}',
                    core_alias,
                    core_run_alias_env.Action(
                        '$UNIT_TEST_RUN_SCRIPT_COMMAND',
                        exitstatfunc = wrap_exit_code_function(
                            core_run_alias_env['RUN_UTEST_EXIT_FUNCTION'], core_run_alias_env, errors.GetPartStackFrameInfo()
                        )
                    )
                )
            sec.Env.AlwaysBuild(core_run_alias)

        base_alias=sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}',core_alias)
        if not skip_run_test:
            base_run_alias=sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}',core_run_alias)
            sec.Env.AlwaysBuild(base_run_alias)


        recurse_alias=sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::',base_alias)
        if not skip_run_test:
            recurse_run_alias=sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::',base_run_alias)
            sec.Env.AlwaysBuild(recurse_run_alias)


        talias=common.map_alias_to_root(sec.Part,'utest','{0}::${{PART_ALIAS_CONCEPT}}{1}::')
        if not skip_run_test:
            talias_run=common.map_alias_to_root(sec.Part,'run_utest','{0}::${{PART_ALIAS_CONCEPT}}{1}::')
            sec.Env.AlwaysBuild(talias_run)


        #Top level
        sec.Env.Alias('${BUILD_UTEST_CONCEPT}',talias)
        if not skip_run_test:
            r=sec.Env.Alias('${RUN_UTEST_CONCEPT}',talias_run)
            sec.Env.AlwaysBuild(r)
    finally:
        parent_obj.DefiningSection=curr_sec
        errors.ResetPartStackFrameInfo()
    sec.LoadState=glb.load_file
    sec._map_targets()
    return ret


def run_utest_return_default(code, env=None, stackframe=None):
    '''
    Callback to be called on unit-test exit.
    @param code: unit-test process exit code.
    @param env: Environment used to define run unit-test Action object.
    @param stackframe: Tuple of (filename, lineno, routine, content).
    '''
    return code

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.UnitTest=unit_test

api.register.add_builder('__UTEST__',SCons.Script.Builder(
        action = SCons.Script.Action(unit_test_script_bf,unit_test_script_bf_str,varlist=[
#            'UNIT_TEST_RUN_COMMAND',
#            'UNIT_TEST_ENV'
            ]),
        emitter=unit_test_script_bfe,
        ))

api.register.add_variable('BUILD_UTEST_CONCEPT','utest${ALIAS_SEPARATOR}','Defines namespace for building a unit test')
api.register.add_variable('RUN_UTEST_CONCEPT','run_utest${ALIAS_SEPARATOR}','Defines namespace for running a unit test')

api.register.add_variable('UTEST_PREFIX','utest-','prefix used by UnitTest to prefix alias name')

api.register.add_variable('UTEST_ALL','$BUILD_UTEST_CONCEPT','Alias used to build all defined unit tests')
api.register.add_variable('RUN_UTEST_ALL','$RUN_UTEST_CONCEPT','Alias used to run all defined unit tests')

api.register.add_variable('UNIT_TEST_ROOT','#_unit_tests','Root path used as sandbox for unit test runs')
api.register.add_variable('UNIT_TEST_DIR',
            '$UNIT_TEST_ROOT/${CONFIG}_${TARGET_PLATFORM}/${PART_NAME}_${PART_VERSION}/$UNIT_TEST_TARGET/',
            'Full directory used for a given unit test run'
            )
api.register.add_list_variable('UTEST_CMDARGS',[],'')
api.register.add_variable('UNIT_TEST_ENV',
            {'UNIT_TEST_DIR':'${ABSPATH("UNIT_TEST_DIR")}'},
            'Default values add to default environment when running unit tests')
api.register.add_variable('UNIT_TEST_TARGET_NAME',
            '${PART_NAME}-${UNIT_TEST_TARGET}_${PART_VERSION}',
            'Default value of a given unit test executable')
api.register.add_variable('UNIT_TEST_SCRIPT_NAME',
            '${UNIT_TEST_TARGET}',
            'Default value of a given unit test executable')
api.register.add_variable('UNIT_TEST_RUN_SCRIPT_COMMAND',
            'cd ${NORMPATH("$UNIT_TEST_DIR")} && ${RELPATH("INSTALL_BIN","UNIT_TEST_DIR")}${UNIT_TEST_TARGET_NAME} ${UTEST_CMDARGS}',
            'Command action used to run a unit test script in SCons run_utest::')
api.register.add_variable('UNIT_TEST_RUN_COMMAND',
        '${RELPATH("INSTALL_BIN","UNIT_TEST_DIR")}${UNIT_TEST_TARGET_NAME} ${UTEST_CMDARGS}',
        'Command action used to run a unit test in the script')
api.register.add_variable('RUN_UTEST_EXIT_FUNCTION',
        run_utest_return_default,
        'Function that will do custom mapping of return code')
