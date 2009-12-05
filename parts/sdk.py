import os
import SCons.Script
import pattern
import common
import exportitem as Xp
import node_helpers

g_sdked_files=set([])

def process_Sdk_Copy(env,target_dir,sources,create_sdk=True,do_clean=False):
    
    # make sure inputs are in good format
    define_part=SCons.Script.DefaultEnvironment().get('DEFINING_PART',None)
    target_dir=env.subst(target_dir)
    # Some varibles
    out=[]
    src_dir=[]
    clean_list=[]
    # not sure we need this anymore
    if do_clean==True:
            clean_list.append(target_dir)
    
    # go through sources to get the source items correctly processed
    for s in sources:
        
        if isinstance(s,pattern.Pattern):
            #print s.sub_dirs()
            t=s.src_dir.srcnode().abspath
            if t not in src_dir:
                src_dir.append(t)
            t,sr=s.target_source(target_dir)
#            for d in s.sub_dirs():
#                final_dir=os.path.join(str(dest_dir),str(d))
#                clean_list.append(final_dir)
            if create_sdk==False:
                out+=sr#s.files(t)
            else:
                out+=env._SDKCOPYAs_(target=t,source=sr)
            
            #print "Pattern type"
        elif isinstance(s,SCons.Node.FS.Dir):
            #get all file in the directory
            #... add code...
            
            t=s.srcnode().abspath
            if t not in src_dir:
                src_dir.append(t)
                #print t
            if create_sdk==False:
                out.append(s)
                #print s
            else:
                #print target_dir,s
                out.extend(env._SDKCOPY_(target=target_dir,source=s))
            #print "Dir type"
        elif isinstance(s,SCons.Node.FS.File):
            #print s.abspath
            t=os.path.split(s.srcnode().abspath)[0]
            if t not in src_dir:
                src_dir.append(t)
                #print t
            if create_sdk==False:
                out.append(s)
                #print s
            else:
                #print target_dir,s
                out.extend(env._SDKCOPY_(target=target_dir,source=s))
            #src.append(s)
            #print "File type"
        elif isinstance(s,SCons.Node.Node) or common.is_string(s):
            t=os.path.split(str(s))[0]
            if t not in src_dir:
                src_dir.append(t)
            if create_sdk==False:
                out.append(s)
            else:
                out.extend(env._SDKCOPY_(target=target_dir,source=s))
            #src.append(s)            
        else:
            def_env=SCons.Script.DefaultEnvironment()
            rpt=def_env['PARTS_REPORTER']
            rpt.part_warning(env,"Unknown type in process_Sdk_Copy() in sdk.py")
        
    #define Alias if we have a part being defined
    if define_part!=None and create_sdk==True:

        # this base alias is made as we need to have the generated sdk file
        # build after all other possible files in the SDK are finished
        sdk_alias_base='_${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+define_part
        sdk_alias='${PART_SDK_CONCEPT}${PART_ALIAS_CONCEPT}'+define_part
        
        # this is the base SDK alias
        sdk_outs=env.Alias(sdk_alias_base,out)
        sdk_outs=env.Alias(sdk_alias,sdk_outs)
        
        # the is for the super alias
        sdk_all=env.Alias("${PART_SDK_CONCEPT}",sdk_outs)
        
        # define the clean
        if clean_list!=[]:
            env.Clean(sdk_all,clean_list)
            env.Clean(sdk_outs,clean_list)
        g_sdked_files.update(out)
        
            
    # return a tuple of output files and the Src_dir list
    # might change this later to a list of the Source file instead
    return (out,src_dir)

    

def SdkItem(env,target_dir,sources,sub_dir='',post_fix='',export_info=[],add_to_path=True,
                auto_add_file=True,use_src_dir=False,use_build_dir=False,create_sdk=True):
       
    if common.is_list(sources)==False:
        sources=[sources]
    sources=SCons.Script.Flatten(sources)
    
    def_env=SCons.Script.DefaultEnvironment()
    define_part=def_env.get('DEFINING_PART',None)
    pinfo=def_env['PART_INFO'][define_part]
    target_paths=[]
    
    if sub_dir=='':
        dest_dir="${PARTSUB('"+define_part+"','"+target_dir+"')}"
        # currenltly we always add that base path, since this is it, 
        # setting to false reduces a extra duplication latter
        add_to_path=False
    else:
        dest_dir=os.path.join("${PARTSUB('"+define_part+"','"+target_dir+"')}",sub_dir)    
    
    do_clean=True
    
    if env['CREATE_SDK'] == False and create_sdk == True:
        create_sdk=False;

    # Process the SDK COPY part of the SDK Item
    targets,source_dir=process_Sdk_Copy(env,dest_dir,sources,create_sdk,do_clean)

    if create_sdk==False and use_build_dir==True:
        target_dir="${PARTSUB('"+define_part+"','$BUILD_DIR')}"
    elif create_sdk==False and use_build_dir==False:
        use_src_dir=True
    
    
    if define_part!=None:
        #Process the Export of data values
        for _type,_prop in export_info:
            # add missing properties in map
            if pinfo.has_key(_prop)==False:
                pinfo[_prop]=[]
            # might add case that allow export of all directories
            if _type==Xp.EXPORT_TYPES.PATH and add_to_path==True:
                target_paths+=Xp.export_path(env,[dest_dir],source_dir,pinfo,_prop,use_src_dir,create_sdk)
                #This line is a hack till we can get a BKM out
                target_paths+=Xp.export_path(env,[target_dir],source_dir,pinfo,_prop,use_src_dir,create_sdk)
            elif _type==Xp.EXPORT_TYPES.PATH and add_to_path==False:
                target_paths+=Xp.export_path(env,[target_dir],source_dir,pinfo,_prop,use_src_dir,create_sdk)
            elif _type==Xp.EXPORT_TYPES.FILE and auto_add_file==True:
                files=Xp.export_file(env,targets,pinfo,_prop)
            elif _type==Xp.EXPORT_TYPES.PATH_FILE:
                files=Xp.export_file_path(env,targets,pinfo,_prop,((create_sdk==False) or use_src_dir))
            else:
                pass
        if create_sdk==True:
            if pinfo.has_key('CREATE_SDK') == False:
                pinfo['CREATE_SDK']=[]
            i=len(export_info)
            if i == 0:
                pass
            elif len(export_info) == 1 and export_info[0][0]==Xp.EXPORT_TYPES.PATH:
                pinfo['CREATE_SDK'].append(('ExportCPPPATH',[common._make_reld(target_paths),False]))
                #pinfo['CREATE_SDK'].append(('SdkItem',[target_dir,common._make_rel([targets[0]]),sub_dir,post_fix,export_info,add_to_path,auto_add_file,True,use_build_dir,False]))    
            else:
                pinfo['CREATE_SDK'].append(('SdkItem',[target_dir,common._make_rel(targets),sub_dir,post_fix,export_info,add_to_path,auto_add_file,True,use_build_dir,False]))
    return targets


def SdkInclude(env,sources,sub_dir='',add_to_path=True,use_src_dir=False,create_sdk=True):

    ret=SdkItem(env,'$SDK_INCLUDE',sources,sub_dir,'',[(Xp.EXPORT_TYPES.PATH ,'CPPPATH')],
            add_to_path=add_to_path,auto_add_file=True,use_src_dir=use_src_dir,
            use_build_dir=False,create_sdk=create_sdk)
    
    return ret
    
    
def SdkLib(env,sources,sub_dir='',add_to_path=True,auto_add_libs=True,use_src_dir=False,create_sdk=True):
    
    ret=SdkItem(env,'$SDK_LIB',sources,sub_dir,'',[(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
            add_to_path=add_to_path,auto_add_file=auto_add_libs,use_src_dir=use_src_dir,
            use_build_dir=True,create_sdk=create_sdk)
    return ret        
    
def SdkBin(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_BIN',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkConfig(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_CONFIG',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret
    
def SdkDoc(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_DOC',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret    

def SdkHelp(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_HELP',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkData(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_DATA',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkMessage(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_MESSAGE',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkResource(env,sources,sub_dir='',create_sdk=True):
    
    ret=SdkItem(env,'$SDK_RESOURCE',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkSample(env, sources, sub_dir='',create_sdk=True):
        
    ret=SdkItem(env,'$SDK_SAMPLE',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkTopLevel(env, sources, sub_dir='',create_sdk=True):

    ret=SdkItem(env,'$SDK_TOP_LEVEL',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkPkgNo(env, sources, sub_dir='',create_sdk=True):

    ret=SdkItem(env,'$SDK_NO_INSTALL',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkAPI(env, sources, sub_dir='',create_sdk=True):

    ret=SdkItem(env,'$SDK_API',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkPython(env, sources, sub_dir='',create_sdk=True):

    ret=SdkItem(env,'$SDK_Python',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret

def SdkScript(env, sources, sub_dir='',create_sdk=True):

    ret=SdkItem(env,'$SDK_Script',sources,sub_dir,'',[],create_sdk=create_sdk)
    return ret


def Sdk(env,sources,sub_dir='',add_to_path=True,auto_add_libs=True,use_src_dir=False,create_sdk=True):
    if sources==None:
        return
    if common.is_list(sources)==False:
        sources=[sources]
    sources=SCons.Script.Flatten(sources)
    out=[]
    for i in sources:
        if isinstance(i,SCons.Node.FS.File)or isinstance(i,SCons.Node.Node) or common.is_string(i):
            if common.is_catagory_file(env,'SDK_LIB_PATTERN',i):
                out+=SdkLib(env,[i],sub_dir=sub_dir,auto_add_libs=auto_add_libs,
                            use_src_dir=use_src_dir,create_sdk=create_sdk)
            elif common.is_catagory_file(env,'SDK_BIN_PATTERN',i):
                out+=SdkBin(env,[i],sub_dir=sub_dir,create_sdk=create_sdk)
            else:
                #print 'Miss',i
                pass
        elif isinstance(i,pattern.Pattern):
            for td in i.sub_dirs():
                for d in i.files(td): 
                    if common.is_catagory_file(env,'SDK_LIB_PATTERN',d):
                        if td !='':
                            out+=SdkItem(env,'$SDK_LIB',[d],os.path.join(str(sub_dir),str(td)),
                                '',[(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
                                add_to_path=add_to_path,auto_add_file=auto_add_libs,use_src_dir=use_src_dir,
                                use_build_dir=True,create_sdk=create_sdk)
                        else:
                            out+=SdkItem(env,'$SDK_LIB',[d], sub_dir,'',
                                [(Xp.EXPORT_TYPES.FILE ,'LIBS'),(Xp.EXPORT_TYPES.PATH ,'LIBPATH')],
                                add_to_path=add_to_path,auto_add_file=auto_add_libs,use_src_dir=use_src_dir,
                                use_build_dir=True,create_sdk=create_sdk)
                            
                        #out+=SdkLib(env,[i],sub_dir=sub_dir,auto_add_libs=auto_add_libs,use_src_dir=use_src_dir,
                        #create_sdk=create_sdk)
                    elif common.is_catagory_file(env,'SDK_BIN_PATTERN',d):
                        if td !='':
                            out+=SdkItem(env,'$SDK_BIN',[d],os.path.join(str(sub_dir),str(td)),'',[],create_sdk=create_sdk)
                        else:
                            out+=SdkItem(env,'$SDK_BIN',[d],sub_dir,'',[],create_sdk=create_sdk)
                        #out+=SdkBin(env,[i],sub_dir=sub_dir,create_sdk=create_sdk)
                    else:
                        pass
    return out

################################################
## SDK BUILDER -- this basically is like Install
## but does a copy... might be able to use newly added Copy builder...
################################################
import tarfile
def untar_print(target, source, env):
    dest=str(source[0])
    destination=os.path.split(dest)[0]
    return  "Unpacking LibPackage files in "+destination
def untar(target, source, env):
    dest=str(source[0])
    destination=os.path.split(dest)[0]    
    tar=tarfile.open(dest,'r')
    tar.extractall(destination)
    tar.close()

def SDKCOPYWrapper(env, target=None, source=None):
    import SCons.Script
    target_factory = env.fs
    try:
        dnodes = env.arg2nodes(target, target_factory.Dir)
    except TypeError:
        raise SCons.Errors.UserError, "PARTS: Target `%s' is a file, but should be a directory.  Perhaps you have the arguments backwards?" % str(dir)
    source=common.make_list(source)
    sources=[]
    # workaround to not having symlinks yet
    for s in source:
        tmp=env.arg2nodes(s, env.fs.Entry)
        symlink=None
        if isinstance(s,SCons.Node.FS.File):
            symlink=env.MetaTagValue(s,'SymLink')
        if symlink is not None:
            env.MetaTag(tmp[0],SymLink=symlink)
        sources.extend(tmp)
        
    #sources = env.arg2nodes(source, env.fs.Entry)
    n_targets = []
    for dnode in dnodes:
        for src in sources:
            # Prepend './' so the lookup doesn't interpret an initial
            # '#' on the file name portion as meaning the Node should
            # be relative to the top-level SConstruct directory.
            symlink=env.MetaTagValue(src,'SymLink')
            if symlink is not None:
                e=env.fs.File('.'+os.sep+src.name, dnode)
                env.MetaTag(e,SymLink=symlink)
                env.MetaTag(e,SymLinkMakeDummyFile=env.MetaTagValue(src,'SymLinkMakeDummyFile',default=True))
            else:
                e=env.fs.Entry('.'+os.sep+src.name, dnode)
            tmp=env.__SDKBuilder__(target=e,source=src)
            n_targets.extend(tmp)
            # hack for gz-so file .. remove later 
            if str(tmp[0]).endswith('.so-gz'):
                n=env.fs.File(str(tmp[0])[:-3])
                env.Command(n,tmp,SCons.Action.Action(untar,untar_print))
    return n_targets


def SDKCOPYAsWrapper(env, target=None, source=None):
    result = []
    for src, tgt in map(lambda x, y: (x, y), source, target):
        result.extend(env.__SDKBuilder__(tgt, src))
    return result

    #n_targets=env.__SDKBuilder__(target=target,source=source)
    #return results

################################################
## SDK BUILDER
################################################

def sdkcopyFunc(dest, source, env):
    import shutil,stat
    if os.path.isdir(source):
        if os.path.exists(dest):
            if not os.path.isdir(dest):
                raise SCons.Errors.UserError, "cannot overwrite non-directory `%s' with a directory `%s'" % (str(dest), str(source))
        else:
            parent = os.path.split(dest)[0]
            if not os.path.exists(parent):
                os.makedirs(parent)
        shutil.copytree(source, dest)
    else:
        if env['HOST_OS']=='win32':
            import win32file
            #try:
            #    win32file.CreateHardLink(dest,source)
            #except:
            win32file.CopyFile(source,dest,False)
        else:
            #try:
            #    os.link(source,dest)
            #except:
                #try:
                #    os.symlink(source,dest)
                #except:
                    shutil.copy2(source, dest)
                    st = os.stat(source)
                    os.chmod(dest, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IWRITE)
        
    return 0

def SDKFunc(target, source, env):
    
    # get the logger for the given part
    output=env["PART_LOG_MAPPER"]    
    # tell it we are starting a task
    id=output.TaskStart(SdkStringFunc(target,source,env)+"\n")
    
    assert( len(target) == len(source) ), "\ntarget: %s\nsource: %s" %(map(str, target),map(str, source))
    for t, s in zip(target, source):
        symlink=env.MetaTagValue(t,'SymLink')
        if symlink is not None:
            node_helpers.make_link_bf([t],None,env)
        elif sdkcopyFunc(t.get_path(), s.get_path(), env):
            #report error to logger
            output.TaskEnd(id,1)
            return 1
    #tell logger the task has end correctly.
    output.TaskEnd(id,0)
    return None

def SdkStringFunc(target, source, env):
    target = str(target[0])
    source = str(source[0])
    if os.path.isdir(source):
        type = 'directory'
    else:
        type = 'file'
    return 'Copying %s: "%s" to SDK as: "%s"' % (type, source, target)

def SdkFuncEmit(target, source, env):
    return ([target[0]], [source[0]])


#####################################################
## The SDK part file builder
#####################################################

def CreateSDK_SF(node, env, path):
    ''' 
    This function is used to map the dependance of the parts file we generate. 
    '''
    ret=[]
    def_env=SCons.Script.DefaultEnvironment()
    alias=env['ALIAS']
    depends=def_env['PART_INFO'][alias]['DEPENDSON']
    for d in depends:
        val=d.resolve_alias(env)
        if val == "":
            #don't need to warn here as it was already warned by primary depends mapper
            continue
        ret.append(def_env['PART_INFO'][val].get('SDK_FILE',def_env['PART_INFO'][val]['FILE']))
    return ret



def CreateSDK_BF(target, source, env):
    def_env=SCons.Script.DefaultEnvironment()

    output=env["PART_LOG_MAPPER"]
    id=output.TaskStart('Generating SDK file for Part '+str(os.path.split(target[0].path)[1][:-9]))
     
    info=def_env['PART_INFO'][env['ALIAS']]
    ver_str=str(info['VERSION'])
    name=env.subst('$PART_SHORT_NAME')
    comp=info['DEPENDSON']
    comp_lst=[]
    sdk_path=os.path.split(target[0].path)[0]
    for c in comp:
        tmp=c.resolve_alias(env)
        if tmp=='':
            exact_ver='*'
        else:
            exact_ver=str(def_env['PART_INFO'][tmp]['VERSION'])
        comp_lst+=['Component("'+c.name+'","'+env.subst(exact_ver)+'",requires='+str(c.requires)+')']

    data='''
#THIS FILE IS AUTO GENERATED
Import('*')
# This is to prevent SDK from generated by mistake another SDK
env['CREATE_SDK'] = False
#This prevents the SDK from being used with different configurations
if not env.isConfigBasedOn("'''+env['CONFIG']+'''"):
    print "Parts generated SDK for part named '''+env.subst('$PART_NAME')+''' (alias of '''+env.subst('$ALIAS')+\
    ''') needs to be build with '''+env['CONFIG']+''' configuration, being build with",env['CONFIG'],"configuration"
    env.Exit(1)
# Normal stuff that all Parts should have
env.PartVersion("'''+ver_str+'''")
env.PartName("'''+name+'''")
env.DependsOn(['''+','.join(comp_lst)+'''])

#Stuff we need to export
'''
    
    for i in info['CREATE_SDK']:
        files=[]
        data+=common.func_gen(env,sdk_path,i[0],i[1])+'\n'
            
    f = open(str(target[0]), 'wb')
    f.write(data)
    f.close()
    output.WriteOut(id,'Done - generating SDK file for Part '+str(os.path.split(target[0].path)[1][:-9])+"\n")
    output.TaskEnd(id,0)
    return None

def CreateSDK_StrF(target, source, env):
    return 'Generating SDK file for Part '+str(os.path.split(target[0].path)[1][:-9])

def CreateSDK_Emit(target, source, env):
    tf= env.subst('$PART_NAME')+'_'+env.subst('$PART_VERSION')
    tout=[os.path.join('$SDK_ROOT',tf+'.sdk.parts')]
    return (tout, source)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.SdkInclude=SdkInclude
SConsEnvironment.SdkLib=SdkLib
SConsEnvironment.SdkBin=SdkBin
SConsEnvironment.Sdk=Sdk
SConsEnvironment.SdkTarget=Sdk
SConsEnvironment.SdkConfig=SdkConfig
SConsEnvironment.SdkDoc=SdkDoc
SConsEnvironment.SdkHelp=SdkHelp
SConsEnvironment.SdkData=SdkData
SConsEnvironment.SdkMessage=SdkMessage
SConsEnvironment.SdkResource=SdkResource
SConsEnvironment.SdkItem=SdkItem
SConsEnvironment.SdkSample=SdkSample
SConsEnvironment.SdkTopLevel=SdkTopLevel
SConsEnvironment.SdkPkgNo=SdkPkgNo
SConsEnvironment.SdkAPI=SdkAPI
SConsEnvironment.SdkPython=SdkPython
SConsEnvironment.SdkScript=SdkScript


SConsEnvironment._SDKCOPY_=SDKCOPYWrapper
SConsEnvironment._SDKCOPYAs_=SDKCOPYAsWrapper

common.AddBuilder('__SDKBuilder__',SCons.Builder.Builder(
        action         = SCons.Action.Action(SDKFunc, SdkStringFunc),
        target_factory = SCons.Node.FS.Entry,
        source_factory = SCons.Node.FS.Entry,
        multi          = 1,
        emitter        = SdkFuncEmit
        ))

common.AddBuilder('__CreateSDKBuilder__',SCons.Builder.Builder(
        action = SCons.Script.Action(CreateSDK_BF,CreateSDK_StrF),
        #target_factory = SCons.Node.FS.File,
        #source_factory = SCons.Node.FS.File,
        emitter=CreateSDK_Emit,
        target_scanner=SCons.Script.DefaultEnvironment().Scanner(CreateSDK_SF)
        ))
import datetime        
# add configuartion varaible
common.AddVariable("DATE_STAMP",datetime.datetime.now().strftime('%Y%m%d%H%M'),'')

common.AddVariable('PART_SDK_CONCEPT','sdk${ALIAS_SEPARTATOR}','')

#common.add_config_var('SDK_ROOT','#sdks/${PART_ROOT_NAME}_${PART_VERSION}${SVN_REVISION==None and DATE_TIME_STAMP or SVN_REVISION}_${ARCHITECTURE}')
common.AddVariable('SDK_ROOT','#sdks/${CONFIG}_${TARGET_PLATFORM}/${PART_ROOT_NAME}_${SVN_REVISION==None and PART_VERSION or PART_VERSION+"."+SVN_REVISION}',
					'Root Directory used for copy SDKs to')
common.AddVariable('SDK_LIB_ROOT','$SDK_ROOT/lib','Full SDK directory for the lib concept')
common.AddVariable('SDK_BIN_ROOT','$SDK_ROOT/bin','Full SDK directory for the bin concept')
common.AddVariable('SDK_INCLUDE_ROOT','$SDK_ROOT/include','Full SDK directory for the include or header concept')
common.AddVariable('SDK_LIB','$SDK_LIB_ROOT','Full SDK directory for the lib concept')
common.AddVariable('SDK_BIN','$SDK_BIN_ROOT','Full SDK directory for the bin concept')
common.AddVariable('SDK_INCLUDE','$SDK_INCLUDE_ROOT','Full SDK directory for the include or header concept')
common.AddVariable('SDK_API','$SDK_ROOT/API','Full SDK directory for the API concept')
common.AddVariable('SDK_CONFIG','$SDK_ROOT/config','Full SDK directory for the configuration file concept')
common.AddVariable('SDK_DOC','$SDK_ROOT/doc','Full SDK directory for the documenation concept')
common.AddVariable('SDK_HELP','$SDK_ROOT/help','Full SDK directory for the help concept')
common.AddVariable('SDK_DATA','$SDK_ROOT/data','Full SDK directory for the generic data concept')
common.AddVariable('SDK_MESSAGE','$SDK_ROOT/message','Full SDK directory for the messages (catalogs) concept')
common.AddVariable('SDK_RESOURCE','$SDK_ROOT/resource','Full SDK directory for the resource concept')
common.AddVariable('SDK_SAMPLE','$SDK_ROOT/sample','Full SDK directory for the sample concept')
common.AddVariable('SDK_TOP_LEVEL','$SDK_ROOT/TOP_LEVEL','Full SDK directory for the file that get installed as the top level (such readme.txt)')
common.AddVariable('SDK_NO_INSTALL','$SDK_ROOT/NO_INSTALL','For files needed for the product in some way, but should not be added in the final install package')
common.AddVariable('SDK_PYTHON','$SDK_ROOT/python','Full SDK directory for the python file concept')
common.AddVariable('SDK_SCRIPT','$SDK_ROOT/scripts','Full SDK directory for general script file concept')

common.AddBoolVariable('USE_SRC_DIR',False,'Controls is the SDK or Src directory of the Part is passed to dependent parts, useful for debug builds')
common.AddBoolVariable('CREATE_SDK',True,'Controls if the SDK should be created and used') 

common.AddListVariable('SDK_LIB_PATTERN',['*.lib','*.LIB','*.a','*.A','*.so','*.sl','*.so.*','*.sl.*','*.so-gz','*.dylib'],'filter of file patterns use to match lib type files')
if 'win32' == SCons.Script.DefaultEnvironment()['PLATFORM']:
    common.AddListVariable('SDK_BIN_PATTERN',['*.dll','*.DLL','*.exe','*.EXE','*.com','*.COM','*.pdb','*.PDB'],'filter of file patterns use to match bin type files')
else:
    common.AddListVariable('SDK_BIN_PATTERN',['*'],'filter of file patterns use to match lib type files')



