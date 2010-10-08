import os,stat
import parts.common as common
import string
import SCons.Script
import parts.core as core
import parts.node_helpers as node_helpers
import parts.pattern as pattern
import parts.functors as functors
import parts.parts as parts
import parts.reporter as reporter 

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
    tout=[os.path.join('$UNIT_TEST_DIR',tf),
        os.path.join('$UNIT_TEST_DIR',tf+'.cmd')
        ]
    
    #env.Clean(env['ALIAS'],tout)
    return (tout,source)

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

env=os.environ   
env.update('''+str(command_env)+''')
cmd=r"'''+cmd+'''"
args=r"'''+env.subst(env['UTEST_CMDARGS'])+'''"
if len(sys.argv) > 1:
    cmd = cmd+" "+string.join(sys.argv[1:],' ')
    print cmd
    env=os.environ
    proc = subprocess.Popen (cmd, env= env,shell=True)
    proc.wait()
else:    
    cmd=cmd+args
    print cmd
    proc = subprocess.Popen (cmd, env= env,shell=True)
    proc.wait()
'''    
    f.write(command)
    f = open(str(target[1]), 'wb')
    f.write("@ECHO OFF\npython "+target[0].abspath)
    f.close()
    st = os.stat(str(target[0]))
    os.chmod(str(target[0]), stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)
    st = os.stat(str(target[1]))
    os.chmod(str(target[1]), stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)
    
    print "PARTS: Writing Test Scripts -- Done"
    

from parts.target_type import target_type
def unit_test(env,target,source,command_args=[],data_src=[],src_dir='.',make_pdb=True,**kw):
        
    #to help with user errors
    reporter.SetPartStackFrameInfo()
    targets=SCons.Script.BUILD_TARGETS
    for t in targets:
        tmp=target_type(t)
        sep_len=len(env.subst("$ALIAS_SEPARTATOR"))
        if tmp.concept == env.subst('$BUILD_UTEST_CONCEPT')[:-sep_len] or tmp.concept == env.subst('$RUN_UTEST_CONCEPT')[:-sep_len]:
            break
    else:
        return []
    
    ## make a new Part object
    parent_obj=common.g_engine._part_manager._from_env(env)
    short_alias=env.subst('${UTEST_PREFIX}%s'%target)
    pobj=parts.Part_t(
        env.subst('${UTEST_PREFIX}%s'%target),
        parent_obj._file,
        create_sdk=False,
        parent_part=parent_obj,
        __is_read=True,
        **kw)
    pobj._setup_(env.Clone(**kw))
    
    common.g_engine._part_manager._add_part(pobj.Alias,pobj)
    # setup basic stuff we need for this part
    
    
    # tweak Environment
    pobj.Env['UNIT_TEST_TARGET']=target
    if src_dir != '.':
        pobj._source_path(node_helpers.AbsDir(env,src_dir))
        
    
    # set the name
    pobj.Env.PartName(short_alias)
    
    ## setup the varible with paths
    curr_path=node_helpers.AbsDir(env,'.')
    orig_src_dir=common.relpath(node_helpers.AbsDir(env,src_dir),curr_path)
    if src_dir!='.':
        src_dir=common.relpath(env.Dir(os.path.join(curr_path,src_dir)).srcnode().abspath,env.Dir('.').abspath)

    build_dir_leaf=pobj.Env['UNIT_TEST_TARGET']
    #build_dir=os.path.join(env.subst('$BUILD_DIR'),build_dir_leaf)
    build_dir=pobj.Env.subst('$BUILD_DIR')
    
    ## map autodepends stuff
    pobj.Env.DependsOn([pobj.Env.Component(env.PartName(),env.PartVersion())])
    
    ## flatten the sources
    source=pobj.Env.Flatten(source)
    
    ## process the sources
    src_files=[]
    for f in source:
        if isinstance(f,pattern.Pattern):
            flst=f.files()
            for i in flst:
                if i[:len(orig_src_dir)]==orig_src_dir:
                    i=i[len(orig_src_dir)+1:]
                src_files.append(os.path.join(build_dir,i))
                
        elif isinstance(f,SCons.Node.FS.Dir):
            pass
        elif isinstance(f,SCons.Node.FS.File) or isinstance(f,SCons.Node.Node):
            src_files.append(f)
        elif common.is_string(f):
            if f[:len(orig_src_dir)]==orig_src_dir:
                f=f[len(orig_src_dir)+1:]
            src_files.append(os.path.join(build_dir,f))
        else:
            reporter.report_warning("Unknown type in unit_test() in unit_test.py in Part",env.subst('$PART_NAME'))
    
    ## flatten the sources
    data_src=pobj.Env.Flatten(data_src)
    
    ## process any data files
    out=[]
    dest_dir="$UNIT_TEST_DIR"
    for s in data_src:
        if isinstance(s,pattern.Pattern):
            t,sr=s.target_source(dest_dir)
            out+=pobj.Env.CCopyAs(target=t,source=sr)
            #print "Pattern type"
        elif isinstance(s,SCons.Node.FS.Dir):
            #get all file in the directory
            #... add code...
            out+=pobj.Env.CCopy(target=dest_dir,source=s)
            #print "Dir type"
        elif isinstance(s,SCons.Node.FS.File):
            out+=pobj.Env.CCopy(target=dest_dir,source=s)
            #print "File type"
        elif isinstance(s,SCons.Node.Node):
            out+=pobj.Env.CCopy(target=dest_dir,source=s)
        elif common.is_string(s):
            if s[:len(orig_src_dir)]==orig_src_dir:
                s=s[len(orig_src_dir)+1:]
            out+=pobj.Env.CCopy(target=dest_dir,source=os.path.join(build_dir,s))
        else:
            reporter.report_warning("Unknown type in unit_test() in unit_test.py in Part",env.subst('$PART_NAME'))

    
    ## the current path
    pobj.Env.Append(CPPPATH= [src_dir]) 
        
    ## change the build dir
    pobj.Env.VariantDir(variant_dir=build_dir,src_dir=src_dir,duplicate=env['duplicate_build'])
    
    ## the option to build with PDB or not
    # might not to do this any more... as teh PDB will work correctly on non windows systems
    if make_pdb==True and pobj.Env['TARGET_PLATFORM'] == 'win32': 
        pobj.Env['PDB']=build_dir+"/"+pobj.Env['UNIT_TEST_TARGET_NAME']+'.pdb'
    else:
        pobj.Env['PDB']=None
    
    ## the unit test we want to build
    ret = pobj.Env.Program(target=build_dir+"/"+pobj.Env['UNIT_TEST_TARGET_NAME'],source=src_files)
    common.tag_node_ownership(pobj.Env,pobj.Env.Dir(build_dir))
    
    #build alias
    build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}'
    a=pobj.Env.Alias("_"+build_alias)     
    
    tmp=[]
    for i in ret:
        if isinstance(i,SCons.Node.FS.File)or isinstance(i,SCons.Node.Node) or common.is_string(i):
            if common.is_catagory_file(pobj.Env,'INSTALL_LIB_PATTERN',i):
                tmp+=pobj.Env.CCopy(target='$INSTALL_LIB',source=i)
            else:#if common.is_catagory_file(env,'SDK_BIN_PATTERN',i):
                tmp+=pobj.Env.CCopy(target='$INSTALL_BIN',source=i)
    ret = tmp
    
     #install alias stuff
    install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+pobj.Alias
    a=env.Alias(install_alias,a+ret)
    # setup basic aliases
    #pobj._map_alias()

    
## finish this below....    
    
    ##make command args string
    cmdargs=" "+string.join(command_args,' ')
    
    ## this builder makes the scripts to run the test on
    ## the command line with ease
    scripts_out=pobj.Env.__UTEST__(build_dir+"/"+pobj.Env['UNIT_TEST_TARGET_NAME'],ret[0].abspath,UTEST_CMDARGS=cmdargs,UNIT_TEST_ENV=env.get('UNIT_TEST_ENV',{}))
    
    ## here we map a bunch of aliases
    
    core_alias=pobj.Env.Alias(pobj.Alias,a+scripts_out+out)
    #add to queue the delayed mapping of any dependent stuff
    common.g_engine.add_preprocess_logic_queue(functors.map_parts_alias(pobj.Env))
    
    base_alias=pobj.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_VERSION}',core_alias)
    base_alias2=pobj.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_SHORT_VERSION}',base_alias)
    base_alias3=pobj.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}'+str(env.PartVersion().major()),base_alias2)
    base_alias4=pobj.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}',base_alias3)
    
    ## map just this test to build
    alias_out=common.make_alias_tree(pobj.Env,'${BUILD_UTEST_CONCEPT}',base_alias,base_alias2,base_alias3,base_alias4)
    test_all_outs=pobj.Env.Alias(pobj.Env['UTEST_ALL'], alias_out)
    pobj._add_alias(pobj.Env['UTEST_ALL'])
    

    ## the command action to Run this stuff
    cmd='$UNIT_TEST_RUN_SCRIPT_COMMAND'
    
    ## map just this test to run    
    # map top level run alias... first one maps to build based 'base_alias'
    base_alias=pobj.Env.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_VERSION}',base_alias,pobj.Env.Action(cmd))
    base_alias2=pobj.Env.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_SHORT_VERSION}',base_alias)
    base_alias3=pobj.Env.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}'+str(env.PartVersion().major()),base_alias2)
    base_alias4=pobj.Env.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}',base_alias3)
    
    env.AlwaysBuild(base_alias)
    env.AlwaysBuild(base_alias2)
    env.AlwaysBuild(base_alias3)
    env.AlwaysBuild(base_alias4)    
    
    #run_alias_out=make_run_alias(env2,None,base_alias)
    run_alias_out=common.make_alias_tree(pobj.Env,'${RUN_UTEST_CONCEPT}',base_alias)
    
    ## map it to all tests to run
    a=pobj.Env.Alias(pobj.Env['RUN_UTEST_ALL'], run_alias_out)
    pobj._add_alias(pobj.Env['RUN_UTEST_ALL'])
    
    ## map the run case to build
    pobj.Env.AlwaysBuild(a)

    reporter.ResetPartStackFrameInfo()
    return ret
    



# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.UnitTest=unit_test

common.AddBuilder('__UTEST__',SCons.Script.Builder(
        action = SCons.Script.Action(unit_test_script_bf,unit_test_script_bf_str),
        emitter=unit_test_script_bfe,
        ))
        
        
# add configuartion varaible
#${BUILD_UTEST_CONCEPT}${ALIAS_SEPARTATOR}

common.AddVariable('BUILD_UTEST_CONCEPT','utest${ALIAS_SEPARTATOR}','Defines namespace for building a unit test')
common.AddVariable('RUN_UTEST_CONCEPT','run_utest${ALIAS_SEPARTATOR}','Defines namespace for running a unit test')

common.AddVariable('UTEST_PREFIX','utest@','prefix used by UnitTest to prefix alias name')

common.AddVariable('UTEST_ALL','$BUILD_UTEST_CONCEPT','Alias used to build all defined unit tests')
common.AddVariable('RUN_UTEST_ALL','$RUN_UTEST_CONCEPT','Alias used to run all defined unit tests')

common.AddVariable('UNIT_TEST_ROOT','#unit_tests','Root path used as sandbox for unit test runs')
common.AddVariable('UNIT_TEST_DIR',
			'$UNIT_TEST_ROOT/${CONFIG}_${TARGET_PLATFORM}/${PART_PARENT_NAME}_${PART_VERSION}/$UNIT_TEST_TARGET_NAME/',
			'Full directory used for a given unit test run'
			)
common.AddVariable('UNIT_TEST_ENV',
			{'UNIT_TEST_DIR':'${ABSPATH("UNIT_TEST_DIR")}'},
			'Default values add to default environment when running unit tests')
common.AddVariable('UNIT_TEST_TARGET_NAME',
			'${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_VERSION}',
			'Default value of a given unit test executable')
common.AddVariable('UNIT_TEST_RUN_SCRIPT_COMMAND',
			'cd ${ABSPATH("UNIT_TEST_DIR")} && python ${UNIT_TEST_TARGET_NAME}',
			'Command action used to run a unit test script in SCons')
common.AddVariable('UNIT_TEST_RUN_COMMAND',
		'cd ${ABSPATH("UNIT_TEST_DIR")} && ${RELPATH("INSTALL_BIN","UNIT_TEST_DIR")}${UNIT_TEST_TARGET_NAME}',
		'Command action used to run a unit test in SCons')
