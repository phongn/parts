import os
import SCons.Script
#import SCons.Environment
import SCons.Tool.install
import pattern
import sdk
import common
import platform_info


def ProcessInstall(env,target,sources,sub_dir,install_alias,create_sdk,sdk_dir='',no_pkg=False):
    installed_files=[]
    src_lst=[]
    
    if sub_dir != '' and sdk_dir != '':
        dest_dir=os.path.join(target, sub_dir)
        pattern_dest_sdk=os.path.join(sdk_dir, sub_dir)
    elif sub_dir != '':
        dest_dir=os.path.join(target, sub_dir)
        pattern_dest_sdk=sdk_dir
    else:
        dest_dir=target
        pattern_dest_sdk=sdk_dir
    
    dest_sdk=sdk_dir
        
    if no_pkg == True:
        tmp_install=SCons.Tool.install._INSTALLED_FILES[:]
        
    if sdk_dir != '':
        for s in sources:
            
            if isinstance(s,pattern.Pattern):
                if s not in sdk.g_sdked_files:
                    if target=='${INSTALL_LIB}':
                        SdkItem(env,'$SDK_LIB',[s],sub_dir,'',[(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
                            add_to_path=True,auto_add_file=True,
                            use_build_dir=True,create_sdk=create_sdk)
                    else:
                        env.SdkItem(dest_sdk,[s],sub_dir,'',[],create_sdk=create_sdk)
                        
                sdkf,sr=s.target_source(pattern_dest_sdk)
                inst,sr=s.target_source(dest_dir)
                #translate the pattern to the install form correctly
                inc=[]
                pdir=env.subst(sdk_dir)
                l=len(pdir)
                for i in sdkf:
                    inc.append(env.File(i).path[l:])
                # src_lst is what is returned to make sure the auto generated SDK work latter.
                # we can use the pattern here for the Install call as the files don't exist in the
                # sdk area during the first run.
                src_lst.append(pattern.Pattern(src_dir=pdir,includes=inc,recursive=s.recursive))
                # take sdk pattrens outputs (targets) as the source and use the same pattern
                # assuming it would copy to the Install area, outputs as the targets
                installed_files.extend(env.InstallAs(inst,sdkf))
                
            elif isinstance(s,SCons.Node.FS.Dir):
                if s not in sdk.g_sdked_files:
                    if target=='${INSTALL_LIB}':
                        ret=SdkItem(env,'$SDK_LIB',[s],sub_dir,'',[(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
                            add_to_path=True,auto_add_file=True,
                            use_build_dir=True,create_sdk=create_sdk)
                    else:
                        ret=env.SdkItem(dest_sdk,[s],sub_dir,'',[],create_sdk=create_sdk)
                else:
                    ret=s
                out=env.Install(dest_dir, ret)
                installed_files.extend(out)
                env.Clean(env.Alias(install_alias), out)
                src_lst.append(env.Dir(ret[0]))
            elif isinstance(s,SCons.Node.FS.File):
                if s not in sdk.g_sdked_files:
                    if target=='${INSTALL_LIB}':
                        ret=SdkItem(env,'$SDK_LIB',[s],sub_dir,'',[(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
                            add_to_path=True,auto_add_file=True,
                            use_build_dir=True,create_sdk=create_sdk)
                    else:
                        ret=env.SdkItem(dest_sdk,[s],sub_dir,'',[],create_sdk=create_sdk)
                else:
                    ret=[s]
                
                installed_files.extend(env.Install(dest_dir, ret))
                src_lst.append(env.File(ret[0]))
            elif isinstance(s,SCons.Node.Node) or common.is_string(s):
                if s not in sdk.g_sdked_files:
                    if target=='${INSTALL_LIB}':
                        ret=SdkItem(env,'$SDK_LIB',[s],sub_dir,'',[(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
                            add_to_path=True,auto_add_file=True,
                            use_build_dir=True,create_sdk=create_sdk)
                    else:
                        ret=env.SdkItem(dest_sdk,[s],sub_dir,'',[],create_sdk=create_sdk)
                else:
                    ret=[s]
                    
                installed_files.extend(env.Install(dest_dir, ret))
                src_lst.append(env.File(ret[0]))
            else:
                rpt.part_warning(env,"Unknown type in ProcessInstall() in installs.py")
        
    
    else:
    
        for s in sources:
            if isinstance(s,pattern.Pattern):
                t,sr=s.target_source(dest_dir)
                installed_files+=env.InstallAs(t,sr)
                src_lst.append(s)
            elif isinstance(s,SCons.Node.FS.Dir):
                out=env.Install(dest_dir, s)
                installed_files+=out
                env.Clean(env.Alias(install_alias), out)
                src_lst.append(env.Dir(s))
            else:
                installed_files+=env.Install(dest_dir, s)
                src_lst.append(env.File(s))                
                
    if no_pkg == True:
        SCons.Tool.install._INSTALLED_FILES=tmp_install
        
    return installed_files,src_lst
        

def InstallItem(env, target, source, sub_dir="" ,sdk_dir='',no_pkg=False,create_sdk=True):
    '''Actually install source files into target location within product
    packaging, and tag with the Part's alias so we know where it came from.

    env         -- the Environment for the Part being processed
    source      -- the file(s) to be installed; can be a single file, a list of
                   files, or a Pattern result
    target      -- the place within the product package to hold source
    returns     -- the return value of the Install call, so that callers can
                   subsequently further Tag these files'''
    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk=False;
    if common.is_list(source)==False:
        source=[source]
    source=SCons.Script.Flatten(source)
    
    def_env=SCons.Script.DefaultEnvironment()
    
    alias=env['ALIAS']
    pinfo=def_env['PART_INFO'][alias]

    
    install_alias='${PART_INSTALL_CONCEPT}${PART_ALIAS_CONCEPT}'+alias        
    installed_files,src_files = ProcessInstall(env,target,source,sub_dir,install_alias,create_sdk,sdk_dir,no_pkg)
    
    
    env.Alias(install_alias,installed_files)

    env.Tag(installed_files, PACKAGING_ALIAS = env['ALIAS'])
    
    if create_sdk:
        if pinfo.has_key('CREATE_SDK') == False:
            pinfo['CREATE_SDK']=[]
        pinfo['CREATE_SDK'].append(('InstallItem',[target, common._make_rel(src_files), sub_dir,"",no_pkg,False]))
    return installed_files


## Do we need to CLEAN these directories??

def InstallTarget(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
    '''Put files into the "executable" area within the product packaging.

    env         -- the Environment for the Part being processed
    src_files   -- the file(s) to be installed; can be a single file, a list of
                   files, or a Pattern result
    sub_dir     -- the optional directory structure to impose'''

    # Look at the Node and its builder and then based on the type of builder
    # we know what kind of thing it is. That's the future direction.


    if common.is_list(src_files)==False:
        src_files=[src_files]
    src_files=SCons.Script.Flatten(src_files)

    installed_files = []

    for i in src_files:
        # We have an individual item
        if isinstance(i,SCons.Node.FS.File) or isinstance(i,SCons.Node.FS.Dir) or isinstance(i,SCons.Node.Node) or common.is_string(i):
            
            if i not in sdk.g_sdked_files:
                ret= env.SdkTarget([i],sub_dir)
            else:
                ret= [i]
        
            if common.is_catagory_file(env, 'INSTALL_LIB_PATTERN', i):
                top_dir = '$INSTALL_LIB'
                #SDK_dir = '$SDK_LIB'
            elif common.is_catagory_file(env, 'INSTALL_BIN_PATTERN', i):
                top_dir = '$INSTALL_BIN'
                #SDK_dir = '$SDK_BIN'
            else:
                continue
            itmp=InstallItem(env, top_dir, ret,sub_dir,
                no_pkg=no_pkg,create_sdk=create_sdk)
            env.Tag(itmp, PACKAGING_TYPE = top_dir[1:])
            installed_files+=itmp
        elif isinstance(i,pattern.Pattern):
            # we have a pattern item
            
            for td in i.sub_dirs():
                if td !='':
                    new_sub_dir=os.path.join(str(sub_dir),str(td))
                else:
                    new_sub_dir=sub_dir
                    
                for d in i.files(td):
                    
                    if d not in sdk.g_sdked_files:
                        ret= env.SdkTarget([d],sub_dir)
                    else:
                        ret= [d]
                    if common.is_catagory_file(env,'INSTALL_LIB_PATTERN',d):
                        top_dir = '$INSTALL_LIB'
                        itmp=InstallItem(env, top_dir,ret,new_sub_dir,
                            no_pkg=no_pkg,create_sdk=create_sdk)                
                        env.Tag(itmp, PACKAGING_TYPE = top_dir[1:])
                        installed_files+=itmp
                    elif common.is_catagory_file(env,'INSTALL_BIN_PATTERN',d):
                        top_dir = '$INSTALL_BIN'
                        itmp=InstallItem(env, top_dir,ret,new_sub_dir,
                            no_pkg=no_pkg,create_sdk=create_sdk)
                        env.Tag(itmp, PACKAGING_TYPE = top_dir[1:])
                        installed_files+=itmp
                    else:
                        pass
        # Unless is_bin_file gets smarter, this will be a problem on Linux
        # since there are no executable extensions there!
        # First we decided to keep going and just blast it into ... UNKNOWN!!
        # Now that filtering is working better, let's just pass on what's left.
        else:
            #print 'Told to InstallTarget', i, '...what should I do?'
            #top_dir = "#UNKNOWN"
            continue
        
    return installed_files


def InstallAPI(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
    installed_files = InstallItem(env, '$INSTALL_API', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_API',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_API')
    return installed_files
    # Need to Tag() as Config? or as part of defining component?


def InstallLib(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):

    installed_files = InstallItem(env, '$INSTALL_LIB', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_LIB',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_LIB')
    return installed_files
    # Need to Tag() as Config? or as part of defining component?
    
def InstallBin(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
    
    installed_files = InstallItem(env, '$INSTALL_BIN', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_BIN',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_BIN')
    return installed_files
    # Need to Tag() as Config? or as part of defining component?


def InstallConfig(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
    
    installed_files = InstallItem(env, '$INSTALL_CONFIG', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_CONFIG',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_CONFIG')
    return installed_files
    # Need to Tag() as Config? or as part of defining component?


def InstallDoc(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
    
    installed_files = InstallItem(env, '$INSTALL_DOC', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_DOC',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_DOC')
    return installed_files
    # Need to Tag() as Doc? or as part of defining component?


def InstallHelp(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):

    installed_files = InstallItem(env, '$INSTALL_HELP', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_HELP',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_HELP')
    return installed_files
    # Need to Tag() as Help? or as part of defining component?


def InstallMessage(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):

    installed_files = InstallItem(env, '$INSTALL_MESSAGE', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_MESSAGE',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_MESSAGE')
    return installed_files
    # Need to Tag() as Message? or as part of defining component?


def InstallResource(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
        
    installed_files = InstallItem(env, '$INSTALL_RESOURCE', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_RESOURCE',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_RESOURCE')
    return installed_files
    # Need to Tag() as Resource? or as part of defining component?


def InstallSample(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
        
    installed_files = InstallItem(env, '$INSTALL_SAMPLE', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_SAMPLE',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_SAMPLE')
    return installed_files
    # Need to Tag() as Sample? or as part of defining component?
    
def InstallData(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):
        
    installed_files = InstallItem(env, '$INSTALL_DATA', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_DATA',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'INSTALL_DATA')
    return installed_files
    # Need to Tag() as Sample? or as part of defining component?


def InstallTopLevel(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):

    installed_files = InstallItem(env, '$INSTALL_TOP_LEVEL', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_TOP_LEVEL',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'TOP_LEVEL')

    return installed_files


def PkgNoInstall(env, src_files, sub_dir='',no_pkg=False,create_sdk=True):

    installed_files = InstallItem(env, '$PKG_NO_INSTALL', src_files,
        sub_dir=sub_dir,sdk_dir='$SDK_NO_INSTALL',no_pkg=no_pkg,create_sdk=create_sdk)
    env.Tag(installed_files, PACKAGING_TYPE = 'NO_INSTALL')
    return installed_files


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.InstallTarget=InstallTarget
SConsEnvironment.InstallAPI=InstallAPI
SConsEnvironment.InstallConfig=InstallConfig
SConsEnvironment.InstallDoc=InstallDoc
SConsEnvironment.InstallData=InstallData
SConsEnvironment.InstallHelp=InstallHelp
SConsEnvironment.InstallMessage=InstallMessage
SConsEnvironment.InstallResource=InstallResource
SConsEnvironment.InstallSample=InstallSample
SConsEnvironment.InstallTopLevel=InstallTopLevel
SConsEnvironment.PkgNoInstall=PkgNoInstall
SConsEnvironment.InstallNoPkg=PkgNoInstall
SConsEnvironment.InstallBin=InstallBin
SConsEnvironment.InstallLib=InstallLib

SConsEnvironment.InstallItem=InstallItem

# add configuartion variable

common.AddVariable('PART_INSTALL_CONCEPT','install${ALIAS_SEPARTATOR}','')

common.AddVariable('INSTALL_ROOT','#install/${CONFIG}_${TARGET_PLATFORM}','')

#these are the replacements
common.AddVariable('INSTALL_LIB','${INSTALL_ROOT}/lib','')
common.AddVariable('INSTALL_BIN','${INSTALL_ROOT}/bin','')

common.AddVariable('INSTALL_API','${INSTALL_ROOT}/API','')
common.AddVariable('INSTALL_INCLUDE','${INSTALL_ROOT}/include','')
common.AddVariable('INSTALL_CONFIG','${INSTALL_ROOT}/config','')
common.AddVariable('INSTALL_DOC','${INSTALL_ROOT}/doc','')
common.AddVariable('INSTALL_HELP','${INSTALL_ROOT}/help','')
common.AddVariable('INSTALL_MESSAGE','${INSTALL_ROOT}/message','')
common.AddVariable('INSTALL_RESOURCE','${INSTALL_ROOT}/resource','')
common.AddVariable('INSTALL_SAMPLE','${INSTALL_ROOT}/sample','')
common.AddVariable('INSTALL_DATA','${INSTALL_ROOT}/data','')
common.AddVariable('INSTALL_TOP_LEVEL','${INSTALL_ROOT}/','')
common.AddVariable('PKG_NO_INSTALL','${INSTALL_ROOT}/NOINSTALL','')

#file patterns
common.AddListVariable('INSTALL_LIB_PATTERN',['*.so','*.sl','*.so.*','*.sl.*'],'')
common.AddListVariable('INSTALL_API_LIB_PATTERN',['*.lib','*.a'],'')

if 'win32' == SCons.Script.DefaultEnvironment()['PLATFORM']:
    common.AddListVariable('INSTALL_BIN_PATTERN',['*.dll','*.DLL','*.exe','*.EXE','*.com','*.COM','*.pdb','*.PDB'],'')
else:
    common.AddListVariable('INSTALL_BIN_PATTERN',['*'],'')


# vim: set et ts=4 sw=4 ai ft=python :
