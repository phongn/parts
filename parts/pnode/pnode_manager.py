
from .. import glb
from .. import datacache
from .. import pickle_helpers
from .. import api

import pnode

import cStringIO
import cPickle
import base64


class manager(object):
    """description of class"""
    
    _node_types={}
    
    def __init__(self):
        self.__known_pnodes={}   # ID:node:parts.pnode 
        self.__known_nodes={}   # ID:SCons.Node.Node
        self.__factories={} # type:function(id)
        self.__aliases={} # ID:Alais node
        #glb.engine.CacheDataEvent+=self.Store
        
    def TotalNode(self):
        return len(self.__known_nodes)
    
    def TotalPnode(self):
        return len(self.__known_pnodes)
        
    def clear_node_states(self):
        for node in self.__known_nodes.itervalues():
            node.clear_memoized_values()
        
    def isKnownNode(self,ID):
        return self.__known_nodes.has_key(ID)
    
    def isKnownPNode(self,ID):
        return self.__known_pnodes.has_key(ID)
    
    def isKnownNodeStored(self,ID):
        data=self._get_cache()
        if data:
            return data['known_nodes'].has_key(ID)
        return False
    
    def isKnownPNodeStored(self,ID):
        data=self._get_cache()
        if data:
            return data['known_pnodes'].has_key(ID)
        return False
            
    def GetNode(self,ID,create=None):
        if self.isKnownNode(ID):
            return self.__known_nodes[ID]
        elif self.isKnownNodeStored(ID):
            return self.LoadNodeStored(ID)
        elif create:
            return self.Create(create,ID)
        return None
    
    def GetPNode(self,ID,create=None):
        if self.isKnownPNode(ID):
            return self.__known_pnodes[ID]
        elif self.isKnownPNodeStored(ID):
            return self.LoadPNodeStored(ID)
        elif create:
            return self.Create(create,ID)
        return None
    
    def LoadNodeStored(self,ID):
        data=self._get_cache()
        if data:
            # get info on the type
            type=data['known_nodes'][ID]['type']
            # make "empty" node based on factory
            node=self.Create(type,ID=ID)
            return node
        return None
    
    def LoadPNodeStored(self,ID):
        data=self._get_cache()
        if data:
            # get info on the type
            type=data['known_pnodes'][ID]['type']
            # make "empty" node based on factory
            node=self.Create(type,ID=ID)
            return node
        return None
    
    def GetAliasStoredInfo(self,ID):
        data=self._get_cache()
        if data:
            return data['aliases'].get(ID)
        return None
            
    
    def GetStoredNodeInfo(self,node):
        data=self._get_cache()
        if data:
            try:
                value=data['known_nodes'][node.ID]['pinfo']
                tmp = base64.b64decode(value)
                buffin=cStringIO.StringIO(tmp)
                upkl=cPickle.Unpickler(buffin)
                upkl.persistent_load =pickle_helpers.persistent_unpickle
                info=upkl.load()    
                info.post_load_convet()
                return info
            except KeyError:
                pass
        return None
    
    def GetStoredPNodeInfo(self,node):
        data=self._get_cache()
        if data:
            try:
                value=data['known_pnodes'][node.ID]['pinfo']
                tmp = base64.b64decode(value)
                buffin=cStringIO.StringIO(tmp)
                upkl=cPickle.Unpickler(buffin)
                upkl.persistent_load =pickle_helpers.persistent_unpickle
                info=upkl.load()
                info.post_load_convet()
                return info
            except KeyError:
                pass
        return None
        
    
    # methods to allow us to track SCons.Nodes
    def AddNodeToKnown(self,node):
        self.__known_nodes[node.ID]=node
        
    def AddPNodeToKnown(self,node):
        self.__known_pnodes[node.ID]=node
    
    def AddAlias(self,node):
        self.__aliases[node.ID]=node
        
    def Aliases(self):
        return self.__aliases
    
    # factory methods
    @classmethod
    def RegisterNodeType(klass,node_type,create_func=None):
        if create_func is None: create_func=pnode.pnode_factory
        klass._node_types[node_type]=create_func
        
    def Create(self,ntype,*lst,**kw):
        return self._node_types[ntype](ntype,*lst,**kw)
    
    # cache data stuff
    
    def dump(self):
        data=stored_data=datacache.GetCache("nodeinfo")
        import pprint
        pp=pprint.PrettyPrinter()
        print "Aliases:"
        for k,v in data['aliases'].iteritems():
            print k,
            pp.pprint(v.__dict__)
        #data['known_nodes']
        for k,v in data['known_nodes'].iteritems():
            tmp = base64.b64decode(v['pinfo'])
            buffin=cStringIO.StringIO(tmp)
            upkl=cPickle.Unpickler(buffin)
            upkl.persistent_load =pickle_helpers.persistent_unpickle
            info=upkl.load()   
            print k,'= ', 
            pp.pprint(info.__dict__)
        #data['known_pnodes']
        for k,v in data['known_pnodes'].iteritems():
            tmp = base64.b64decode(v['pinfo'])
            buffin=cStringIO.StringIO(tmp)
            upkl=cPickle.Unpickler(buffin)
            upkl.persistent_load =pickle_helpers.persistent_unpickle
            info=upkl.load()   
            print k,'= ',
            pp.pprint(info.__dict__)
    
    def _get_cache(self):
        stored_data=datacache.GetCache("nodeinfo")
        return stored_data
    
    def Store(self,goodexit):
        
        if goodexit==False:
            return
        
        def store_value(node,_info,valuestostore):
            try:
                buffout=cStringIO.StringIO()
                pkl=cPickle.Pickler(buffout)
                pkl.persistent_id=pickle_helpers.persistent_pickle
                pkl.dump(_info)
                tmp= buffout.getvalue()
                info = base64.b64encode(tmp)
                valuestostore[node.ID]={
                    'type':node.__class__,
                    'pinfo':info
                    }
            except cPickle.PicklingError,e:
                #ec_str=StringIO.StringIO()
                #traceback.print_exc(file=ec_str)
                api.output.warning_msg('Can\'t save Unpickle-able data for node "{0}" {1}'.format(node.ID,e))
        
        
        data={}
        stored_data=self._get_cache()
        
        valuestostore= {} if stored_data is None else stored_data.get('aliases',{})
        store_all=valuestostore == {}
        for k,node in self.__aliases.iteritems():
            if node.isVisited or store_all:
                binfo = node.get_binfo()
                # translate the node objects to a string value
                for a in ['bsources', 'bdepends', 'bimplicit']:
                    try:
                        val = getattr(binfo, a)
                    except AttributeError:
                        pass
                    else:
                        setattr(binfo, a, list(map(node_to_str, val)))
                valuestostore[node.ID]=binfo
        data['aliases']=valuestostore
        
        from .. import  metatag
        valuestostore= {} if stored_data is None else stored_data.get('known_nodes',{})
        store_all=valuestostore == {}
        for k,node in self.__known_nodes.copy().iteritems():
            if node.isVisited or store_all:
                if isinstance(node,SCons.Node.Alias.Alias) and node.Stored:
                    newvalue=metatag.MetaTagValue(node,'components',ns='partinfo',default={})
                    
                    for k1,v in newvalue.iteritems():
                        try:
                            node.Stored.components[k1].update(v)
                        except KeyError:
                            node.Stored.components[k1]=v
                    store_value(node,node.Stored,valuestostore)
                else:
                    store_value(node,node.GenerateStoredInfo(),valuestostore)
                
                
            
        # this is the set of all nodes type
        data['known_nodes']=valuestostore
        
        valuestostore= {} if stored_data is None else stored_data.get('known_pnodes',{})
        store_all=valuestostore == {}
        for k,node in self.__known_pnodes.copy().iteritems():
            if node._remove_cache:
                del valuestostore[node.ID]
            elif (node.LoadState==glb.load_file) or store_all:
                sd=node.GenerateStoredInfo()
                #import section
                #import difflib
                #import StringIO
                #tmpstr=StringIO.StringIO()
                #tmpstr2=StringIO.StringIO()
                #if node.Stored and isinstance(node,section.section):
                  #if node.Stored.exports!=sd.exports:
                    #import pprint                    
                    #print "node info is different",node
                    #pprint.pprint(node.Stored.exports,tmpstr)
                    #print "stored:"
                    #print tmpstr.getvalue()
                    #pprint.pprint(sd.exports,tmpstr2)
                    #print "new   :"
                    #print tmpstr2.getvalue()
                        
                    #for dd in difflib.unified_diff(tmpstr.getvalue().split(),tmpstr2.getvalue().split()):
                    #    print dd
                    
                store_value(node,sd,valuestostore)
                
        
        # this is the set of all nodes type
        data['known_pnodes']=valuestostore
        datacache.StoreData("nodeinfo",data)
        
import SCons.Node
import os
        
def node_to_str(node):
    if isinstance(node,SCons.Node.FS.File):
        t=node.path
        t.replace(os.sep, '/')
        return t
    elif isinstance(node,SCons.Node.FS.Dir):
        t=node.path
        t.replace(os.sep, '/')
        return t
    elif isinstance(node,SCons.Node.FS.Entry):        
        t=node.path
        t.replace(os.sep, '/')
        return t
    elif SCons.Util.is_String(node):        
        t=node
        t.replace(os.sep, '/')
        return t
    elif isinstance(node,SCons.Node.Python.Value):
        return node.value
    elif isinstance(node,SCons.Node.Alias.Alias):
        return node.name
    else:
        print "unknown type",node,type(node)
    return None        
    
#glb.pnodes=manager()

        