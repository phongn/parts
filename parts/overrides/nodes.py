from .. import glb
from .. import errors
from .. import common
from .. import api
from .. import datacache
from ..pnode import scons_node_info
from ..pnode import pnode_manager
from .. import metatag

import SCons.Node

import itertools
import os
import hashlib
import pprint

Node=SCons.Node.Node
File=SCons.Node.FS.File
Dir=SCons.Node.FS.Dir
Entry=SCons.Node.FS.Entry
FSBase=SCons.Node.FS.Base
Value=SCons.Node.Python.Value
Alias=SCons.Node.Alias.Alias

    
class wrapper(object):
    def __init__(self,binfo,ninfo=None):
        self.binfo=binfo
        self.ninfo=ninfo

#
#def env_set(self,env,safe=False):
#    ''' This function allows use to map which Part/Component should be assigned a given Node
#    
#    It shoudl be noted that this API is a only called by the Builder. So ever Node that has an 
#    Environment as a builder and as such is a Target of some build action. Everything else is a 
#    Source node that is on disk.
#    '''
#    self.orig_env_set(env,safe)
#    #if env.hasMetaTag(self,'owners','parts') ==False:# and\
#    #    #(isinstance(self,SCons.Node.FS.File) or isinstance(self,SCons.Node.FS.Dir)):
#    #    alias=env.get("PART_ALIAS",None)
#    #    if alias:
#    #        pobj=self.__part_manager.parts[alias]
#    #        if self.has_builder():
#    #            add_builder_context_files(pobj,self.builder)
#    #        # add node to set of known nodes for this component    
#    #        pobj._part_nodes.add(v)
#    #1/0
#
#
#SCons.Node.Node.orig_env_set=SCons.Node.Node.env_set
#SCons.Node.Node.env_set=env_set
#

def make_path_ID(path):
    t=path
    return t.replace(os.sep, '/')
    return t

class fake_ninfo(object):
    __slots__=['timestamp','csig']
    def __init__(self,timestamp,csig):
        self.timestamp=timestamp
        self.csig=csig

Node.make_ninfo_from_dict=lambda self,dict:fake_ninfo(dict.get('timestamp',0),dict.get('csig',0))

#def _node_up_to_date(node,ninfo):
#    ''' 
#    Expects a Scons node objects, will test aginst stored info 
#    to see if it is uptodate
#    '''
#        
#    try:
#        class fake_ninfo(object):
#            #__slots__=['timestamp','csig']
#            def __init__(self,timestamp,csig):
#                self.timestamp=timestamp
#                self.csig=csig
#        tninfo=fake_ninfo(ninfo['timestamp'],ninfo['csig'])
#        ninfo=tninfo
#    except:
#        pass
#
#    print ninfo.__dict__
#    # see if node time stamp matches
#    tmp=getattr(ninfo,'timestamp',None)
#    if tmp is None:
#        s="'%s' does not exist in the SCons DB"%(node)
#        #metatag.MetaTag(node,ns='parts',uptodate=s)
#        api.output.verbose_msg("update_check",s)
#        return False
#    if node.exists() == False:
#        s="'%s' does not exist"%(node)
#        #metatag.MetaTag(node,ns='parts',uptodate=s)
#        api.output.verbose_msg("update_check",s)
#        return False
#    if node.get_timestamp() != tmp:
#        # timestamp did not match.. try md5
#        api.output.verbose_msg("update_check","TimeStamp diff in '%s'"%(node))
#        if node.get_csig() != getattr(ninfo,'csig',0):
#            # md5 failure
#            #print ninfo.__dict__,node.get_csig()
#            s="%s is out of date because of differences"%(node)
#            #metatag.MetaTag(node,ns='parts',uptodate=s)
#            api.output.verbose_msg("update_check",s)
#            return False
#    #api.output.verbose_msg("update_check","%s seems to be unmodified"%(node))
#    #metatag.MetaTag(node,ns='parts',uptodate=True)
#    return True

#SCons.Node.Node.is_same_since=_node_up_to_date


# as it turns out this testing before Scons maps a Environment to a node is broken
# to fix it we will map the Node Class default function ourself
# other wise it go through a Environment proxy, which can be a NULL class that does nothing
# not we only do this for the File as all other values at the moment
File.changed_since_last_build = File.changed_timestamp_then_content




total=0

def _part_isUpToDate(self):
    ''' 
    '''
    global total
    total+=1
    try:
        tmp=self._memo['_part_isUpToDate']
        return tmp
    except KeyError:
        #print total,"->", self.ID
        def check_nodes(data):
            nodelist=[]
            ret=False
            # get the set of node object from str value
            for j,k in data:
                if common.is_string(k):
                    # this is a string.. we want to make it a SCons Node
                    # look it up in our DB
                    i=glb.pnodes.GetNode(k) 
                    #i=j.str_to_node(k)
                    # not found... possible the path was stored with bad "/" values
                    if i is None: 
                        # try again
                        i=glb.pnodes.GetNode(make_path_ID(k))
                        if i is None: 
                            #This might be a source node, with some builder that
                            # that output in a "wrong" place.
                            # see if it exists
                            if os.path.exists(k):
                                #it exists.. make a entry node
                                i=glb.pnodes.Create(Entry,k)
                            else:
                                api.output.verbose_msg("update_check",'{0} out-of-date! {1} is not known'.format(self.ID,k))
                                return False
                            
                    i.disambiguate()
                    
                    if isinstance(i,SCons.Node.FS.Base):
                        
                        st_info=i.get_stored_info()
                        #Scons is  not storing information on source node
                        # this tends to be an issue with Directories used as sources
                        if st_info is None and isinstance(i,SCons.Node.FS.Dir):
                            # we skip this at the moment
                            continue
                        nbinfo=i.get_stored_info().binfo
                            
                        if not os.path.exists(i.path) and not os.path.exists(i.srcnode().path) and \
                            nbinfo.bsourcesigs == [] and \
                            nbinfo.bdependsigs == [] and \
                            nbinfo.bimplicitsigs ==[] :  
                            # we need to figure out the real source file and check it
                            # load from our cache information as SCons does not store this
                            # relationship. It assume the file are read in fully
                            # so any test it has are done one fully setup nodes
                            storedpinfo=i.Stored
                            if storedpinfo:
                                n=storedpinfo.SrcNode(i)
                                #api.output.verbose_msg("update_check",'getting src node for {0}\n {1} '.format(i.ID,n.ID))
                                n._memo['get_stored_info']=i._memo['get_stored_info']
                                i.clear()
                                i=n
                else:
                    i=k     
                    try:
                        j=k.get_stored_info().ninfo
                    except AttributeError:
                        if isinstance(k,Alias):
                            binfo=glb.pnodes.GetAliasStoredInfo(k.ID)
                            if binfo:
                                k._memo['get_stored_info']=wrapper(binfo)
                            j=k.get_stored_info().ninfo
                        
                        
                nodelist.append((i,j))
            #########
            # sort list
            nodelist.sort(key=hash)
            ##########
            #process the list of nodes
            md5=hashlib.md5()
            for i in nodelist:
                # test to see if it thinks it is out of date
                if not i[0].pisUpToDate:
                    api.output.verbose_msg("update_check",'{0} out-of-date! SCons Node "{1}" says it is out of date'.format(self.ID,i[0]))
                    return False
                
                # we test if this is out of date from the local point of view
                if isinstance(i[0],FSBase):
                    if not i[0].exists():
                        api.output.verbose_msg("update_check",'{0} out-of-date! "{1}" does not exist'.format(self.ID,i[0]))
                        return False
                    elif i[0].changed_since_last_build(self,i[1]):#_node_up_to_date(i[0],i[1]):
                        #print i[0].get_ninfo().__dict__,i[1].__dict__#,i[0].get_csig()
                        api.output.verbose_msg("node_update_check",'{0} out-of-date! "{1}" is different since this node was last built'.format(self.ID,i[0]))
                        return False
                
            return True
        
        try:
            binfo=self.get_stored_info().binfo
        except AttributeError:
            # this is probally an Value I was loading from my parts DB
            binfo=self.get_binfo()            
        
        # see if anything this node depends on is out of date, if so we are out of date
        nodes=itertools.izip(binfo.bsourcesigs+binfo.bdependsigs+binfo.bimplicitsigs,
            getattr(binfo,'bsources',[])+getattr(binfo,'bdepends',[])+getattr(binfo,'bimplicit',[]))
            
        if not check_nodes(nodes):
            self._memo['_part_isUpToDate'] = False
            return self._memo['_part_isUpToDate'] 
        
        # check any side effect nodes
        if self.Stored:
            side_effects=self.Stored.side_effects
            for node in side_effects:
                if not node.pisUpToDate:
                    api.output.verbose_msg("update_check",'{0} out-of-date! Side effect target {1} is out of date'.format(self.ID,node.ID))
                    self._memo['_part_isUpToDate'] = False
                    return self._memo['_part_isUpToDate'] 
                    
                #if self.changed_since_last_build(self,ninfo):#_node_up_to_date(self,ninfo):
                    #api.output.verbose_msg("node_update_check",'{0} out-of-date! out of date with itself'.format(self.ID))
                    #self._memo['_part_isUpToDate'] = False
                    #return self._memo['_part_isUpToDate'] 

        # are we out of date
        #if isinstance(self,FSBase):
        #    if not self.exists():
        #        api.output.verbose_msg("update_check",'{0} out-of-date! Does not exist!'.format(self.ID))
        #        self._memo['_part_isUpToDate'] = False
        #        return self._memo['_part_isUpToDate'] 
            
        #api.output.verbose_msg("node_update_check",'{0} is up to date!'.format(self.ID))
        self._memo['_part_isUpToDate'] = True
        return self._memo['_part_isUpToDate'] 


SCons.Node.Node.pisUpToDate=property(_part_isUpToDate)


# built replacement (wrapper)
def parts_built(self):
    self._orig_built()
    #say this built Parts know to update this nodes info
    self.isBuilt=True
    

Node._orig_built=Node.built
Node.built=parts_built
#File._orig_built=File.built
#File.built=parts_built
#Dir._orig_built=Dir.built
#Dir.built=parts_built

def _get_isbuilt(self):
    return getattr(self,'_isBuilt',False)

def _set_isbuilt(self,value):
    self._isBuilt=value

SCons.Node.Node.isBuilt=property(_get_isbuilt,_set_isbuilt)


# visited replacement
def parts_visited(self):      
    self.get_csig()   
    #if self.isVisited:
        #return

    #self.clear_memoized_values()
    self._orig_visited()
    #say this built Parts know to update this nodes info
    self.isVisited=True
    
Node._orig_visited=Node.visited
Node.visited=parts_visited
File._orig_visited=File.visited
File.visited=parts_visited
#Dir._orig_visited=Dir.visited
#Dir.visited=parts_visited

def part_stat(self):
    ''' 
    This function replaces the built in SCons stat function to allow me an ability to deal with Symlinks better
    This function is set after the init call of the Node to work around an ugly issue.
    '''
    try: 
        return self._memo['stat']
    except KeyError: 
        try:
                
            if glb.engine._build_mode=='build' and (metatag.MetaTagValue(self,'SymLink',default=False) or getattr(self.Stored,'issymlink',False)):
                result = os.lstat(self.abspath)
            else:
                result = os.stat(self.abspath)
        except os.error: 
            result = None
        self._memo['stat'] = result
    return result

FSBase.pstat=part_stat

#############################################
## these are pnode addition

def _get_isVisited(self):
    return getattr(self,'_isVisited',False)

def _set_isVisited(self,value):
    self._isVisited=value

SCons.Node.Node.isVisited=property(_get_isVisited,_set_isVisited)

def _get_FSID(self):
    t=self.path
    return t.replace(os.sep, '/')

def _get_ValueID(self):
    return "{0}".format(self.value)
    
def _get_AliasID(self):
    return self.name

SCons.Node.FS.Base.ID=property(_get_FSID)
SCons.Node.Python.Value.ID=property(_get_ValueID)
SCons.Node.Alias.Alias.ID=property(_get_AliasID)


def _my_init(self,name, directory, fs):
    self.orig_init(name, directory, fs)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddNodeToKnown(self)
    self.stat=self.pstat
    # just in case the state was set we want to remove it and force it to be recached
    try :
        del self._memo['stat']
    except:
        pass

SCons.Node.FS.Base.orig_init=SCons.Node.FS.Base.__init__
SCons.Node.FS.Base.__init__=_my_init

#SCons.Node.FS.Dir.orig_init=SCons.Node.Node.__init__
#SCons.Node.FS.Dir.__init__=_my_init

#SCons.Node.FS.Entry.orig_init=SCons.Node.Node.__init__
#SCons.Node.FS.Entry.__init__=_my_init

def _my_init(self, value, built_value=None):
    self.orig_init( value, built_value)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddNodeToKnown(self)

SCons.Node.Python.Value.orig_init=SCons.Node.Python.Value.__init__
SCons.Node.Python.Value.__init__=_my_init

def _my_init(self,name):
    self.orig_init(name)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddAlias(self)
    glb.pnodes.AddNodeToKnown(self)
    
    binfo=glb.pnodes.GetAliasStoredInfo(self.ID)
    if binfo:
        self._memo['get_stored_info']=wrapper(binfo)

SCons.Node.Alias.Alias.orig_init=SCons.Node.Alias.Alias.__init__
SCons.Node.Alias.Alias.__init__=_my_init


def parts_node_hash(self):
    return hash(self.ID)
    
SCons.Node.Node.__hash__=parts_node_hash

def get_stored_info_alias(self):
    return self._memo.get('get_stored_info')

SCons.Node.Alias.Alias.get_stored_info=get_stored_info_alias

def Stored(self):
    
    try:
        return self.__stored
    except AttributeError:
        try:
            self.__stored=self.LoadStoredInfo()
        except errors.LoadStoredError:
                self.__stored=None
    
    return self.__stored
    
SCons.Node.Node.Stored=property(Stored)
    
def LoadStoredInfo(self):
    return glb.pnodes.GetStoredNodeInfo(self)
    #md5=hashlib.md5()
    #md5.update(self.ID)
    #stored_data=datacache.GetCache("snode-{0}".format(md5.hexdigest()))
    #return stored_data

SCons.Node.Node.LoadStoredInfo=LoadStoredInfo
        
def StoreStoredInfo(self):
    pass
    #info=self.GenerateStoredInfo()
    #md5=hashlib.md5()
    #md5.update(self.ID)
    #datacache.StoreData("snode-{0}".format(md5.hexdigest()),info)
    
SCons.Node.Node.StoreStoredInfo=StoreStoredInfo
        
    
def GenerateStoredInfo(self):
    info = scons_node_info.scons_node_info()
    info.type=self.__class__
    info.components=metatag.MetaTagValue(self,'components',ns='partinfo',default={})
    info.side_effects=self.side_effects # these are nodes that need to be checked for
    info.issymlink=metatag.MetaTagValue(self,'SymLink',default=False)
    if isinstance(self,FSBase):
        if self.ID != self.srcnode().ID:
            info.srcnode=self.srcnode()
    return info

SCons.Node.Node.GenerateStoredInfo=GenerateStoredInfo

# these are "factories" to allow Parts to recreate the Node from cache latter.

def Scons_fsnode_factory(func,ID=None,*lst,**kw):
    if ID:
        return func(ID,'#')
    else:
        return func(ID,*lst,**kw)

def Scons_node_factory(func,ID=None,*lst,**kw):
    if ID:
        return func(ID)
    else:
        return func(ID,*lst,**kw)
    
def Scons_alias_node_factory(func,ID=None,*lst,**kw):

    if ID:
        tmp=func(ID)[0]
    else:
        tmp=func(ID,*lst,**kw)[0]
    #binfo=glb.pnodes.GetAliasStoredInfo(tmp.ID)
    #if binfo:
        #tmp._memo['get_stored_info']=wrapper(binfo)
    
    return tmp

pnode_manager.manager.RegisterNodeType(File, lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().File,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Dir,  lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().Dir,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Entry,lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().Entry,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Value,lambda x,*lst,**kw: Scons_node_factory(SCons.Script.DefaultEnvironment().Value,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Alias,lambda x,*lst,**kw: Scons_alias_node_factory(SCons.Script.DefaultEnvironment().Alias,*lst,**kw))

