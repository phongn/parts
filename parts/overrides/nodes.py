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


# as it turns out this testing before Scons maps a Environment to a node is broken
# to fix it we will map the Node Class default function ourself
# other wise it go through a Environment proxy, which can be a NULL class that does nothing
# not we only do this for the File as all other values at the moment
File.changed_since_last_build = File.changed_timestamp_then_content


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
        try:
            if self.ID != self.srcnode().ID:
                info.SrcNodeID=self.srcnode().ID
        except:
            pass

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

