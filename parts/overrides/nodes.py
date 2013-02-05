from .. import glb
from .. import errors
from .. import common
from .. import api
from .. import datacache
from ..pnode import scons_node_info
from ..pnode import pnode_manager
from .. import metatag
from .. import node_helpers

from SCons.Debug import logInstanceCreation

import SCons.Node
import SCons.Util
SCons.Node.NodeList = SCons.Util.NodeList

import itertools
import os
import hashlib
import pprint
import stat

# Import symlinks to make sure it patches SCons.Node.FS and SCons.Environment before
# we refer it
import symlinks

Node=SCons.Node.Node
File=SCons.Node.FS.File
Dir=SCons.Node.FS.Dir
Entry=SCons.Node.FS.Entry
FileSymbolicLink=SCons.Node.FS.FileSymbolicLink
FSBase=SCons.Node.FS.Base
Value=SCons.Node.Python.Value
Alias=SCons.Node.Alias.Alias


class wrapper(object):
    def __init__(self,binfo,ninfo=None):
        if __debug__: logInstanceCreation(self)
        self.binfo=binfo
        self.ninfo=ninfo

def make_path_ID(path):
    t=path
    return t.replace(os.sep, '/')
    return t

class fake_ninfo(object):
    __slots__=['timestamp','csig','__weakref__']
    def __init__(self,timestamp,csig):
        if __debug__: logInstanceCreation(self)
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
                    if i is None and '\\' in k:
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
                            api.output.verbose_msgf("update_check",'{0} out-of-date! {1} is not known',self.ID,k)
                            return False

                    i.disambiguate()

                    if isinstance(i,SCons.Node.FS.Base):

                        st_info=i.get_stored_info()
                        #Scons is  not storing information on source node
                        # this tends to be an issue with Directories used as sources
                        if st_info is None and isinstance(i,Dir):
                            # we skip this at the moment
                            continue
                        nbinfo=st_info.binfo

                        if not i.exists() and not i.srcnode().exists() and \
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
                                api.output.verbose_msg("update_check",'Getting src node for {0}\n {1} '.format(i.ID,n.ID))
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
                            try:
                                j=k.get_stored_info().ninfo
                            except AttributeError:
                                j=k.get_ninfo()



                nodelist.append((i,j))
            #########
            # sort list
            #nodelist.sort(key=hash)
            ##########
            #process the list of nodes
            for i in nodelist:
                api.output.verbose_msgf("update_check_extra",'{0} checking for changes in node {0}',self.ID,i[0])
                # test to see if it thinks it is out of date
                if not i[0].pisUpToDate:
                    api.output.verbose_msgf("update_check",'{0} out-of-date! SCons Node "{1}" says it is out of date',self.ID,i[0])
                    return False

                # we test if this is out of date from the local point of view
                if isinstance(i[0],FSBase):
                    if not i[0].exists():
                        api.output.verbose_msgf("update_check",'{0} out-of-date! "{1}" does not exist',self.ID,i[0])
                        return False
                    else:
                        api.output.verbose_msgf("update_check_extra",'{0} -- "{1}" does exist',self.ID,i[0])
                    if i[0].changed_since_last_build(self,i[1]):#_node_up_to_date(i[0],i[1]):
                        #print i[0].get_ninfo().__dict__,i[1].__dict__#,i[0].get_csig()
                        api.output.verbose_msgf("update_check",'{0} out-of-date! "{1}" is different since this node was last built',self.ID,i[0])
                        return False
                    else:
                        api.output.verbose_msgf("update_check_extra",'{0} -- "{1}" does not look like it changed',self.ID,i[0])

            return True
        # End of check_nodes procedure

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


        if self.Stored:
            # check for AlwaysBuild State
            if self.Stored.AlwaysBuild:
                api.output.verbose_msgf("update_check",'{0} out-of-date! Because AlwaysBuild() was called on node',self.ID)
                self._memo['_part_isUpToDate'] = False
                return self._memo['_part_isUpToDate']
            # check any side effect nodes
            side_effects=self.Stored.SideEffectIDs
            for nodeid in side_effects:
                node=glb.pnodes.GetNode(nodeid)
                if not node.pisUpToDate:
                    api.output.verbose_msgf("update_check",'{0} out-of-date! Side effect target {1} is out of date',self.ID,node.ID)
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
    #self.get_csig()

    #self.clear_memoized_values()
    self._orig_visited()

    if not self.isVisited:
        # this is target node we just built
        # store the information
        glb.pnodes.StoreNode(self)
        try:
            # might be a custom node type that does not have am
            # srcnode concept
            tmp=self.srcnode()
            tmp.isVisited=True
            if tmp!=self:
                glb.pnodes.StoreNode(tmp)
        except AttributeError:
            pass

    self.isVisited=True


def parts_alias_visited(self):
    # Visited get called twice in current Scon logic
    if not self.isVisited:
        glb.pnodes.StoreAlias(self)
    self._orig_alias_visited()


Node._orig_visited=Node.visited
Node.visited=parts_visited
File._orig_visited=File.visited
File.visited=parts_visited
#Dir._orig_visited=Dir.visited
#Dir.visited=parts_visited
Alias._orig_alias_visited=Alias.visited
Alias.visited=parts_alias_visited

#############################################
## these are pnode addition

def _get_isVisited(self):
    return getattr(self,'_isVisited',False)

def _set_isVisited(self,value):
    self._isVisited=value

SCons.Node.Node.isVisited=property(_get_isVisited,_set_isVisited)

def _get_FSID(self):
    try:
        return self.__FSID
    except AttributeError:
        self.__FSID = self.path.replace(os.sep, '/')
        return self.__FSID

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

SCons.Node.FS.Base.orig_init=SCons.Node.FS.Base.__init__
SCons.Node.FS.Base.__init__=_my_init

#SCons.Node.FS.Dir.orig_init=SCons.Node.Node.__init__
#SCons.Node.FS.Dir.__init__=_my_init

def def_FS_Entry___init__(klass):
    orig = klass.__init__
    def __init__(self, name, directory, fs):
        if __debug__: logInstanceCreation(self, 'Node.FS.Entry')
        orig(self, name, directory, fs)
    klass.__init__ = __init__
def_FS_Entry___init__(SCons.Node.FS.Entry)

def _my_init(self, value, built_value=None):
    if __debug__: logInstanceCreation(self, 'Node.Python.Value')
    self.orig_init( value, built_value)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddNodeToKnown(self)

SCons.Node.Python.Value.orig_init=SCons.Node.Python.Value.__init__
SCons.Node.Python.Value.__init__=_my_init

def map_alias_stored(obj):
    binfo=glb.pnodes.GetAliasStoredInfo(obj.ID)
    if binfo:
        obj._memo['get_stored_info']=wrapper(binfo)

def _my_init(self,name):
    if __debug__: logInstanceCreation(self, 'Node.Alias.Alias')
    self.orig_init(name)
    # may not be the best way.. but works for the moment
    glb.pnodes.AddAlias(self)
    glb.pnodes.AddNodeToKnown(self)

    if glb.engine.isSconstructLoaded:
        map_alias_stored(self)
    else:
        glb.engine.SConstructLoadedEvent+=lambda build_mode : map_alias_stored(self)

SCons.Node.Alias.Alias.orig_init=SCons.Node.Alias.Alias.__init__
SCons.Node.Alias.Alias.__init__=_my_init


def parts_node_hash(self):
    try:
        return self._hash
    except AttributeError:
        self._hash = hash(self.ID)
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

SCons.Node.Node.LoadStoredInfo=LoadStoredInfo

def StoreStoredInfo(self):
    pass

SCons.Node.Node.StoreStoredInfo=StoreStoredInfo


def GenerateStoredInfo(self):
    info = scons_node_info.scons_node_info()
    info.Type=self.__class__
    info.Components=metatag.MetaTagValue(self,'components',ns='partinfo',default={}).copy()
    for partid,sections in info.Components.iteritems():
        tmp=set([sec.ID for sec in sections])
        info.Components[partid]=tmp

    info.SideEffectIDs=[i.ID for i in self.side_effects] # these are nodes that need to be checked for

    info.AlwaysBuild=self.always_build==True
    if isinstance(self,FSBase):
        if self.ID != self.srcnode().ID:
            info.SrcNodeID=self.srcnode().ID

    binfo=self.get_binfo()
    nodes=itertools.izip(getattr(binfo,'bsources',[])+getattr(binfo,'bdepends',[])+getattr(binfo,'bimplicit',[]),
                            binfo.bsourcesigs+binfo.bdependsigs+binfo.bimplicitsigs)
    new_binfo={}

    for node,ninfo in nodes:
        # some time the node info is a string not a Node object
        try:
            key=node.ID
        except:
            # for some reason SCons will store the Alias "children" values as strings
            # not Nodes. This mean that the children of File nodes may not be normalized to
            # the expected value
            # if the node is not known.. we probally want to swap the
            # os.sep value to a posix forms
            if not glb.pnodes.isKnownNode(node):
                key=node.replace(os.sep, '/')
            else:
                key=node
            node=glb.pnodes.GetNode(key)

        if isinstance(self,Alias) and isinstance(node,FSBase):
            ninfo=node.get_ninfo()

        new_binfo[key]={
                        'timestamp':getattr(ninfo,'timestamp',0),
                        'csig':getattr(ninfo,'csig',0)
                        }

    info.SourceInfo=new_binfo

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

pnode_manager.manager.RegisterNodeType(File,         lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().File,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Dir,          lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().Dir,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Entry,        lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().Entry,*lst,**kw))
pnode_manager.manager.RegisterNodeType(FileSymbolicLink,        lambda x,*lst,**kw: Scons_fsnode_factory(SCons.Script.DefaultEnvironment().FileSymbolicLink,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Value,        lambda x,*lst,**kw: Scons_node_factory(SCons.Script.DefaultEnvironment().Value,*lst,**kw))
pnode_manager.manager.RegisterNodeType(Alias,        lambda x,*lst,**kw: Scons_alias_node_factory(SCons.Script.DefaultEnvironment().Alias,*lst,**kw))

