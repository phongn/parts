import os,stat
import parts.common as common
import string
import SCons.Script
import parts.core as core
import parts.node_helpers as node_helpers
import parts.pattern as pattern
import parts.functors as functors
import parts.parts

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
    #rel_path=common.relpath(os.path.split(source[0].abspath)[0],os.path.split(target[0].abspath)[0])
    #cmd=os.path.join(rel_path,os.path.split(source[0].abspath)[1])
    cmd=env.subst("$UNIT_TEST_RUN_COMMAND")
    command_env=env.get('UNIT_TEST_ENV',{})
    #print env.subst("$UNIT_TEST_RUN_COMMAND")
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
    


def unit_test(env,target,source,command_args=[],data_src=[],src_dir='.',make_pdb=True,**kw):
    
    ## make a new enviroment to prevent conflicts with pdb files and output names
    #env2=core.generate_config({},{},kw)
    env2=env.Clone(**kw)
    def_env=SCons.Script.DefaultEnvironment()

    ## extra mapping for unit testing
    env2['UNIT_TEST_TARGET']=target
      
    short_alias=env2.subst('${UTEST_PREFIX}${UNIT_TEST_TARGET}')
    
    old_val=def_env['DEFINING_PART']

    ## some basic mappings we want from the orginal part
    ## probally need more, might want to think about how to refactor this 
    ##common.g_env_w_builders.add(id(env2))
    part_info=parts.parts.make_part_info(env2,None,short_alias,env['ALIAS'])
    #small hack to help with error messages
    part_info['FILE']=env['PART_INFO']['FILE']
    part_info['MAKES_SDK']=False
    #part_info['BASE_PATH']=env['PART_INFO']['BASE_PATH']
    
    alias=env2['ALIAS']
    def_env['PART_INFO'][alias]=part_info
    #helps with debugging
    env2['PART_INFO']=part_info

    ### clean this up
    ##alias info
    env2['PART_ALIAS']=part_info['ALIAS']
    env2['PART_ROOT_ALIAS']=part_info['ROOT_ALIAS']
    env2['PART_PARENT_ALIAS']=part_info['PARENT_ALIAS']
    
    ## name info
    env2['PART_NAME']="${PARTS('"+alias+"','NAME')}"
    env2['PART_SHORT_NAME']="${PARTS('"+alias+"','SHORT_NAME')}"    
    env2['PART_ROOT_NAME']="${PARTS('"+alias+"','ROOT_NAME')}"
    env2['PART_PARENT_NAME']="${PARTS('"+alias+"','PARENT_NAME')}"

    ## version info
    env2['PART_VERSION']="${PARTS('"+alias+"','VERSION')}"
    env2['PART_SHORT_VERSION']="${PARTS('"+alias+"','SHORT_VERSION')}"
    

    env2.PartName(short_alias)
    ## setup the varible with paths
    curr_path=node_helpers.AbsDir(env,'.')
    orig_src_dir=common.relpath(node_helpers.AbsDir(env,src_dir),curr_path)
    if src_dir!='.':
        src_dir=common.relpath(env.Dir(os.path.join(curr_path,src_dir)).srcnode().abspath,env.Dir('.').abspath)

    build_dir_leaf=env2['UNIT_TEST_TARGET']
    #build_dir=os.path.join(env.subst('$BUILD_DIR'),build_dir_leaf)
    build_dir=env2.subst('$BUILD_DIR')
    

    ##map autodepends stuff
    env2.DependsOn([env2.Component(env.PartName(),env.PartVersion())])
    
    ## flatten the sources
    source=env.Flatten(source)
    
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
            print "Unknown type in unit_test() in unit_test.py"
    
    ## flatten the sources
    data_src=env.Flatten(data_src)
    
    ## process any data files
    out=[]
    dest_dir="$UNIT_TEST_DIR"
    for s in data_src:
        if isinstance(s,pattern.Pattern):
            t,sr=s.target_source(dest_dir)
            out+=env2._SDKCOPYAs_(target=t,source=sr)
            #print "Pattern type"
        elif isinstance(s,SCons.Node.FS.Dir):
            #get all file in the directory
            #... add code...
            out+=env2._SDKCOPY_(target=dest_dir,source=s)
            #print "Dir type"
        elif isinstance(s,SCons.Node.FS.File):
            out+=env2._SDKCOPY_(target=dest_dir,source=s)
            #print "File type"
        elif isinstance(s,SCons.Node.Node):
            out+=env2._SDKCOPY_(target=dest_dir,source=s)
        elif common.is_string(s):
            if s[:len(orig_src_dir)]==orig_src_dir:
                s=s[len(orig_src_dir)+1:]
            out+=env2._SDKCOPY_(target=dest_dir,source=os.path.join(build_dir,s))
        else:
            print "Parts: Warning! -- Unknown type in unit_test() in unit_test.py in Part",env.subst('$PART_NAME')

    
    ## the current path
    env2.Append(CPPPATH= [src_dir]) 
        
    ## change the build dir
    env2.VariantDir(variant_dir=build_dir,src_dir=src_dir,duplicate=env['duplicate_build'])
    
    ## the option to build with PDB or not
    if make_pdb==True and env2['PLATFORM'] == 'win32': 
        env2['PDB']=build_dir+"/"+env2['UNIT_TEST_TARGET_NAME']+'.pdb'
    else:
        env2['PDB']=None
    
    ## the unit test we want to build
    ret = env2.Program(target=build_dir+"/"+env2['UNIT_TEST_TARGET_NAME'],source=src_files)
    
    # build alias stuff
    if common.g_name_alias_map.has_key(alias) == False:
        common.g_name_alias_map[alias]=set()
    # add to set of known aliases
    common.g_name_alias_map[alias].add(alias)
    
    build_alias='${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}'
    a=env2.Alias("_"+build_alias,ret)        
    common.g_name_alias_map[alias].add("_"+build_alias)
    
    tmp=[]
    for i in ret:
        if isinstance(i,SCons.Node.FS.File)or isinstance(i,SCons.Node.Node) or common.is_string(i):
            if common.is_catagory_file(env,'INSTALL_LIB_PATTERN',i):
                tmp+=env2._SDKCOPY_(target='$INSTALL_LIB',source=i)
            else:#if common.is_catagory_file(env,'SDK_BIN_PATTERN',i):
                tmp+=env2._SDKCOPY_(target='$INSTALL_BIN',source=i)
    ret = tmp
    
     #install alias stuff
    install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+alias
    a=env.Alias(install_alias,a+ret)
    common.g_name_alias_map[alias].add(install_alias)
    
## finish this below....    
    
    ##make command args string
    cmdargs=" "+string.join(command_args,' ')
    
    ## this builder makes the scripts to run the test on
    ## the command line with ease
    scripts_out=env2.__UTEST__(build_dir+"/"+env2['UNIT_TEST_TARGET_NAME'],ret[0].abspath,UTEST_CMDARGS=cmdargs,UNIT_TEST_ENV=env.get('UNIT_TEST_ENV',{}))
    
    ## here we map a bunch of aliases
    
    core_alias=env2.Alias(alias,a+scripts_out+out)
    #add to queue the delayed mapping of any dependent stuff
    def_env['PREPROCESS_LOGIC_QUEUE'].append(functors.map_parts_alias(env2))
    
    base_alias=env2.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_VERSION}',core_alias)
    base_alias2=env2.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_SHORT_VERSION}',base_alias)
    base_alias3=env2.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}'+str(env.PartVersion().major()),base_alias2)
    base_alias4=env2.Alias('${BUILD_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}',base_alias3)
    
    ## map just this test to build
    #alias_out=make_build_alias(env2,base_alias,base_alias2,base_alias3,base_alias4)
    alias_out=common.make_alias_tree(env2,'${BUILD_UTEST_CONCEPT}',base_alias,base_alias2,base_alias3,base_alias4)
    test_all_outs=env2.Alias(env2['UTEST_ALL'], alias_out)
    common.g_name_alias_map[alias].add(env2['UTEST_ALL'])
    

    ## the command action to Run this stuff
    cmd='$UNIT_TEST_RUN_SCRIPT_COMMAND'
    
    ## map just this test to run    
    # map top level run alias... first one maps to build based 'base_alias'
    base_alias=env2.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_VERSION}',base_alias,env2.Action(cmd))
    base_alias2=env2.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}_${PART_SHORT_VERSION}',base_alias)
    base_alias3=env2.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}'+str(env.PartVersion().major()),base_alias2)
    base_alias4=env2.Alias('${RUN_UTEST_CONCEPT}${PART_PARENT_NAME}@${UNIT_TEST_TARGET}',base_alias3)
    
    env.AlwaysBuild(base_alias)
    env.AlwaysBuild(base_alias2)
    env.AlwaysBuild(base_alias3)
    env.AlwaysBuild(base_alias4)    
    
    #run_alias_out=make_run_alias(env2,None,base_alias)
    run_alias_out=common.make_alias_tree(env2,'${RUN_UTEST_CONCEPT}',base_alias)
    
    ## map it to all tests to run
    a=env2.Alias(env2['RUN_UTEST_ALL'], run_alias_out)
    common.g_name_alias_map[alias].add(env2['RUN_UTEST_ALL'])
    
    ## map the run case to build
    env2.AlwaysBuild(a)

    def_env['DEFINING_PART']=old_val
    return ret


def make_build_alias(env,name_version,
    name_shortversion=None,
    name_majorversion=None,
    name_only=None):
    

    # utest::$PART_NAME_$VERSION
    name='${BUILD_UTEST_CONCEPT}${PART_NAME}_${PART_VERSION}'
    #print 'mapping',env.subst(name),'->',name_version[0]
    n_ver_alias=env.Alias(name, name_version)
    # utest::$PART_NAME_$SHORT_VERSION
    
    name='${BUILD_UTEST_CONCEPT}${PART_NAME}_${PART_SHORT_VERSION}'
    if name_shortversion == None:
        #print 'mapping',env.subst(name),'->',n_ver_alias[0]
        n_sver_alias=env.Alias(name, n_ver_alias)
    else:
        #print 'mapping',env.subst(name),'->',n_ver_alias[0],name_shortversion[0]
        n_sver_alias=env.Alias(name, [n_ver_alias,name_shortversion])
        
    # utest::$PART_NAME_$MAJOR_VERSION
    name='${BUILD_UTEST_CONCEPT}${PART_NAME}_'+str(env.PartVersion().major())
    if name_majorversion == None:
        #print 'mapping',env.subst(name),'->',n_sver_alias[0]
        n_mver_alias=env.Alias(name, n_sver_alias)
    else:
        #print 'mapping',env.subst(name),'->',n_sver_alias[0],name_majorversion[0]
        n_mver_alias=env.Alias(name, [n_sver_alias,name_majorversion])
    # utest::$PART_NAME
    name='${BUILD_UTEST_CONCEPT}${PART_NAME}'
    if name_only == None:
        #print 'mapping',env.subst(name),'->',n_mver_alias[0]
        name_alias=env.Alias(name, n_mver_alias)
    else:
        #print 'mapping',env.subst(name),'->',n_mver_alias[0],name_only[0]
        name_alias=env.Alias(name, [n_mver_alias,name_only])
    
    # clean up thsi statement once we clean up the Part vars
    if env['PART_INFO']['PARENT_ALIAS'] != None:
        def_env=SCons.Script.DefaultEnvironment()
        parent_env=def_env['PART_INFO'][env['PART_INFO']['PARENT_ALIAS']]['ENV']
        return make_build_alias(parent_env,n_ver_alias,n_sver_alias,n_mver_alias,name_alias)
    
    return name_alias
    
    
def make_run_alias(env,action,name_version,
    name_shortversion=None,
    name_majorversion=None,
    name_only=None):
    

    # utest::$PART_NAME_$VERSION
    runname='${RUN_UTEST_CONCEPT}${PART_NAME}_${PART_VERSION}'
    #print 'mapping',env.subst(runname),'->',name_version[0]
    if action ==None:
        n_ver_alias=env.Alias(runname, name_version)
    else:
        n_ver_alias=env.Alias(runname, name_version, action)
    
    # utest::$PART_NAME_$SHORT_VERSION
    runname='${RUN_UTEST_CONCEPT}${PART_NAME}_${PART_SHORT_VERSION}'
    if name_shortversion == None:
        #print 'mapping',env.subst(runname),'->',n_ver_alias[0]
        n_sver_alias=env.Alias(runname, n_ver_alias)
    else:
        #print 'mapping',env.subst(runname),'->',n_ver_alias[0],name_shortversion[0]
        n_sver_alias=env.Alias(runname, [n_ver_alias,name_shortversion])
        
    # utest::$PART_NAME_$MAJOcoolR_VERSION
    runname='${RUN_UTEST_CONCEPT}${PART_NAME}_'+str(env.PartVersion().major())
    if name_majorversion == None:
        #print 'mapping',env.subst(runname),'->',n_sver_alias[0]
        n_mver_alias=env.Alias(runname, n_sver_alias)
    else:
        #print 'mapping',env.subst(runname),'->',n_sver_alias[0],name_majorversion[0]
        n_mver_alias=env.Alias(runname, [n_sver_alias,name_majorversion])
    # utest::$PART_NAME
    runname='${RUN_UTEST_CONCEPT}${PART_NAME}'
    if name_only == None:
        #print 'mapping',env.subst(runname),'->',n_mver_alias[0]
        name_alias=env.Alias(runname, n_mver_alias)
    else:
        #print 'mapping',env.subst(runname),'->',n_mver_alias[0],name_only[0]
        name_alias=env.Alias(runname, [n_mver_alias,name_only])

    # make it run all the time
    env.AlwaysBuild(n_ver_alias)
    env.AlwaysBuild(n_sver_alias)
    env.AlwaysBuild(n_mver_alias)
    env.AlwaysBuild(name_alias)
    
    # clean up thsi statement once we clean up the Part vars
    if env['PART_INFO']['PARENT_ALIAS'] != None:
        def_env=SCons.Script.DefaultEnvironment()
        parent_env=def_env['PART_INFO'][env['PART_INFO']['PARENT_ALIAS']]['ENV']
        return make_run_alias(parent_env,None,n_ver_alias,n_sver_alias,n_mver_alias,name_alias)
    
    return name_alias

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
