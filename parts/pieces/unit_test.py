
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

import os,stat
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

    silent = SCons.Script.GetOption('silent')
    if silent:
      printcmd = ""
    else:
      printcmd = "print cmd"
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
    '''+printcmd+'''
    env=os.environ
    proc = subprocess.Popen (cmd, env= env,shell=True)
    proc.wait()
else:    
    cmd=cmd+args
    '''+printcmd+'''
    proc = subprocess.Popen (cmd, env= env,shell=True)
    proc.wait()
'''    
    f.write(command)
    f = open(str(target[1]), 'wb')
    f.write("@ECHO OFF\npython "+target[0].abspath+" %*")
    f.close()
    st = os.stat(str(target[0]))
    os.chmod(str(target[0]), stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)
    st = os.stat(str(target[1]))
    os.chmod(str(target[1]), stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)
    
    

from parts.target_type import target_type
def unit_test(env,target,source,command_args=[],data_src=[],src_dir='.',make_pdb=True,**kw):
        
    #to help with user errors
    errors.SetPartStackFrameInfo()

    if ("utest::" in env["SUPPRESS_SECTION"] or 
        "utest" in env["SUPPRESS_SECTION"] or 
        "run_utest::" in env["SUPPRESS_SECTION"] or 
        "run_utest" in env["SUPPRESS_SECTION"]) and \
        SCons.Script.GetOption('section_suppression'):
        api.output.verbose_msgf("warning",'Skipping the processing of Part section "utest" in Part {0}',env.PartName())
        return []

    targets=SCons.Script.BUILD_TARGETS
    for t in targets:
        tmp=target_type(t)
        sep_len=len(env.subst("$ALIAS_SEPARTATOR"))
        if tmp.Section == 'utest':
            break
    else:
        return []
    
    
    ## make a new Part object
    parent_obj=glb.engine._part_manager._from_env(env)
    sec= parent_obj.Section("utest")
    #if sec.Name!='utest':
    short_alias=env.subst('${UTEST_PREFIX}%s'%target)
    sec=glb.pnodes.Create(pnode.section.utest_section,parent_obj,env=env.Clone(**kw))
    parent_obj._AddSection("utest",sec)
        #sec._setup_(parent_obj,env=env.Clone(**kw))
    
    curr_sec=parent_obj.DefiningSection
    parent_obj.DefiningSection=sec
        
    
    
    # tweak Environment
    sec.Env['UNIT_TEST_TARGET']=target
    
     ## setup the varible with paths
    curr_path=node_helpers.AbsDir(env,'.')
    orig_src_dir=common.relpath(node_helpers.AbsDir(env,src_dir),curr_path)
    if src_dir!='.':
        src_dir=common.relpath(env.Dir(os.path.join(curr_path,src_dir)).srcnode().abspath,env.Dir('.').abspath)
    else:
        src_dir=curr_path

    build_dir_leaf=sec.Env['UNIT_TEST_TARGET']
    build_dir=sec.Env.subst("{0}/{1}".format('$BUILD_DIR',build_dir_leaf))
    
    ## map autodepends stuff
    sec.Env.DependsOn([sec.Env.Component(env.PartName(),env.PartVersion(),section='build')])
    
    ## flatten the sources
    source=sec.Env.Flatten(source)
    
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
            if s[:len(orig_src_dir)]==orig_src_dir:
                s=s[len(orig_src_dir)+1:]
            out+=sec.Env.CCopy(target=dest_dir,source=os.path.join(build_dir,s))
        else:
            api.output.warning_msg("Unknown type in unit_test() in unit_test.py in Part",env.subst('$PART_NAME'))

    ## the current path
    sec.Env.Append(CPPPATH= [src_dir]) 
        
    ## change the build dir
    sec.Env.VariantDir(variant_dir=build_dir,src_dir=src_dir,duplicate=env['duplicate_build'])
    
    ## the option to build with PDB or not
    # might not to do this any more... as the PDB will work correctly on non windows systems
    if make_pdb==True: 
        sec.Env['PDB']=build_dir+"/"+sec.Env['UNIT_TEST_TARGET_NAME']+'.pdb'
    else:
        sec.Env['PDB']=None
        
    ## the unit test we want to build
    ret = sec.Env.Program(target=build_dir+"/"+sec.Env['UNIT_TEST_TARGET_NAME'],source=src_files)
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
    
     #install alias stuff
    #install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+sec.Alias
    #a=env.Alias(build_alias,ret)
    # setup basic aliases
    #pobj._map_alias()

    
    ##make command args string
    cmdargs=" "+string.join(command_args,' ')
    
    ## this builder makes the scripts to run the test on
    ## the command line with ease
    scripts_out=sec.Env.__UTEST__(build_dir+"/_scripts_/"+sec.Env['UNIT_TEST_SCRIPT_NAME'],ret[0].abspath,UTEST_CMDARGS=cmdargs,UNIT_TEST_ENV=env.get('UNIT_TEST_ENV',{}))
    scripts_out=sec.Env.CCopy("$UNIT_TEST_DIR",scripts_out)
    ### here we map a bunch of aliases
    core_alias=sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}',a+scripts_out+out+ret)
    ## the command action to Run this stuff
    cmd='$UNIT_TEST_RUN_SCRIPT_COMMAND'
    # map top level run alias... first one maps to build based 'base_alias'
    core_run_alias=sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}',core_alias,sec.Env.Action(cmd))
    sec.Env.AlwaysBuild(core_run_alias)
    #add to queue the delayed mapping of any dependent stuff
    glb.engine.add_preprocess_logic_queue(functors.map_parts_alias(sec.Env))
    
    base_alias=sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}',core_alias)
    base_run_alias=sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}',core_run_alias)
    sec.Env.AlwaysBuild(base_run_alias)
    
    
    recurse_alias=sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::',base_alias)
    recurse_run_alias=sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::',base_run_alias)
    sec.Env.AlwaysBuild(recurse_run_alias)
    
    
    talias=common.map_alias_to_root(sec.Part,'utest','{0}::${{PART_ALIAS_CONCEPT}}{1}::')
    talias_run=common.map_alias_to_root(sec.Part,'run_utest','{0}::${{PART_ALIAS_CONCEPT}}{1}::')
    sec.Env.AlwaysBuild(talias_run)
    
    
    #Top level
    sec.Env.Alias('${BUILD_UTEST_CONCEPT}',talias)
    r=sec.Env.Alias('${RUN_UTEST_CONCEPT}',talias_run)
    sec.Env.AlwaysBuild(r)
    parent_obj.DefiningSection=curr_sec
    errors.ResetPartStackFrameInfo()
    sec.LoadState=glb.load_file
    return ret
       
  


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.UnitTest=unit_test

api.register.add_builder('__UTEST__',SCons.Script.Builder(
        action = SCons.Script.Action(unit_test_script_bf,unit_test_script_bf_str),
        emitter=unit_test_script_bfe,
        ))
        
        
# add configuartion varaible
#${BUILD_UTEST_CONCEPT}${ALIAS_SEPARTATOR}

api.register.add_variable('BUILD_UTEST_CONCEPT','utest${ALIAS_SEPARTATOR}','Defines namespace for building a unit test')
api.register.add_variable('RUN_UTEST_CONCEPT','run_utest${ALIAS_SEPARTATOR}','Defines namespace for running a unit test')

api.register.add_variable('UTEST_PREFIX','utest-','prefix used by UnitTest to prefix alias name')

api.register.add_variable('UTEST_ALL','$BUILD_UTEST_CONCEPT','Alias used to build all defined unit tests')
api.register.add_variable('RUN_UTEST_ALL','$RUN_UTEST_CONCEPT','Alias used to run all defined unit tests')

api.register.add_variable('UNIT_TEST_ROOT','#_unit_tests','Root path used as sandbox for unit test runs')
api.register.add_variable('UNIT_TEST_DIR',
            '$UNIT_TEST_ROOT/${CONFIG}_${TARGET_PLATFORM}/${PART_NAME}_${PART_VERSION}/$UNIT_TEST_TARGET/',
            'Full directory used for a given unit test run'
            )
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
            'cd ${ABSPATH("UNIT_TEST_DIR")} && python ${UNIT_TEST_SCRIPT_NAME}',
            'Command action used to run a unit test script in SCons run_utest::')
api.register.add_variable('UNIT_TEST_RUN_COMMAND',
        'cd ${ABSPATH("UNIT_TEST_DIR")} && ${RELPATH("INSTALL_BIN","UNIT_TEST_DIR")}${UNIT_TEST_TARGET_NAME}',
        'Command action used to run a unit test in the script')
