import glb
import pnode.pnode
import requirement

import SCons.Script
import SCons.Node.FS

import os
import cPickle
import copy_reg
import types
import base64
import cStringIO

def node_to_str(node):
    if isinstance(node,SCons.Node.FS.File):
        t=node.ID
        return t.replace(os.sep, '/')

    elif isinstance(node,SCons.Node.FS.Dir):
        t=node.ID
        return t.replace(os.sep, '/')

    elif isinstance(node,SCons.Node.FS.Entry):
        t=node.ID
        return t.replace(os.sep, '/')

    elif SCons.Util.is_String(node):
        t=node.ID
        return t.replace(os.sep, '/')

    elif isinstance(node,SCons.Node.Python.Value):
        return node.ID
    elif isinstance(node,SCons.Node.Alias.Alias):
        return node.ID
    else:
        print "unknown type",node,type(node)
    return None

def node_typestr(node):
    if isinstance(node,SCons.Node.FS.File):
        return 'File'
    elif isinstance(node,SCons.Node.FS.Dir):
        return 'Dir'
    elif isinstance(node,SCons.Node.FS.Entry):
        return 'Entry'
    elif isinstance(node,SCons.Node.Python.Value):
        return 'Value'
    elif isinstance(node,SCons.Node.Alias.Alias):
        return 'Alias'
    return None


def node_type(s):
    if s=='File':
        return SCons.Node.FS.File
    elif s=='Dir':
        return SCons.Node.FS.Dir
    elif s=='Entry':
        return SCons.Node.FS.Entry
    elif s=='Value':
        return SCons.Node.Python.Value
    elif s=='Alias':
        return SCons.Node.Alias.Alias
    return None



def unpickle_node(node):
    ''' recreate a node object.. hopefully mapped to an existing object in SCons FS manager'''
    ntype,value=node.split("::",1)
    tmp=glb.pnodes.GetNode(value)
    if tmp:
        return tmp
    else:
        return glb.pnodes.Create(node_type(ntype),value)

    raise cPickle.UnpicklingError,'Unknown Node Type {0} {1}'.format(ntype,value)


def pickle_node(node):
    '''pickles a node object into a form we can use to have SCons remake the node again'''

    ntype=node_typestr(node)
    value=node_to_str(node)
    if ntype is None:
        raise cPickle.PicklingError, 'Unknown Node Type {0}'.format(type(node))
    #Parts#NODE:
    return "{0}::{1}".format(ntype,value)


def unpickle_pnode(nodeid):
    ''' recreate a pnode object..'''
    return glb.pnodes.GetPNode(nodeid)

def pickle_pnode(node):
    '''pickles a node object into a form we can use to have SCons remake the node again'''
    return "{0}".format(node.ID)

def unpickle_req(data):
    ''' recreate a pnode object..'''
    tmp=requirement.REQ()
    tmp = base64.b64decode(data)
    buffin=cStringIO.StringIO(tmp)
    upkl=cPickle.Unpickler(buffin)
    upkl.persistent_load =persistent_unpickle
    info=upkl.load()
    tmp=requirement.REQ()
    return tmp.Unserialize(info)

def pickle_req(req):
    '''pickles a node object into a form we can use to have SCons remake the node again'''
    data=req.Serialize()
    buffout=cStringIO.StringIO()
    pkl=cPickle.Pickler(buffout)
    pkl.persistent_id=persistent_pickle
    pkl.dump(data)
    tmp= buffout.getvalue()
    return base64.b64encode(tmp)


def persistent_pickle(obj):
    import pnode.section

    if isinstance(obj,SCons.Node.Node):
        return "node::{0}".format(pickle_node(obj))
    #elif isinstance(obj,pnode.pnode.pnode):
    #    return "pnode::{0}".format(pickle_pnode(obj))
    #elif isinstance(obj,requirement.REQ):
    #    return "REQ::{0}".format(pickle_req(obj))
    return None


def persistent_unpickle(perid):
    ntype,value=perid.split("::",1)
    if ntype == 'node':
        return unpickle_node(value)
    #elif ntype == 'pnode':
    #    return unpickle_pnode(value)
    #elif ntype == 'REQ':
    #    return unpickle_req(value)
    else:
        raise cPickle.UnpicklingError, 'Unknown custom pickle Type {0}'.format(ntype)


## function pickle helpers

def pickle_function(func):
    buffout=cStringIO.StringIO()
    pkl=cPickle.Pickler(buffout)
    pkl.dump(obj.func_code)
    tmp= buffout.getvalue()
    tmp = base64.b64encode(tmp)
    return tmp

def unpickle_function(func):
    tmp = base64.b64decode(func)
    buffin=cStringIO.StringIO(tmp)
    upkl=cPickle.Unpickler(buffin)
    tmp=upkl.load()
    return types.FunctionType(tmp,def_globals)

def persistent_id(obj):
    if isinstance(obj,SCons.Node.Node):
        tmp=pickle_node(obj)
        if tmp:
            return 'Parts@NODE@'+tmp
        else:
            raise cPickle.PicklingError, "Failed to pickle a node object"
    elif isinstance(obj,types.FunctionType ):
            tmp= pickle_function(obj)
            return 'Parts@FunctionType@'+tmp
    return None

def persistent_load(persid):

    if persid.startswith('Parts@NODE@'):
        tmp=persid[len('Parts@NODE@'):]
        return unpickle_node(tmp)
    elif persid.startswith('Parts@FunctionType@'):
        tmp=persid[len('Parts@FunctionType@'):]
        return unpickle_function(tmp)
    else:
        raise pickle.UnpicklingError, 'Invalid persistent id'

## this code allow use to handle the pickle of byte code
## the other way we can do this is to use a libray
## to grab the source code, given that we would always have
## source at run time this might be a better solution.

def unpickle_code(*data):
    return types.CodeType(*data)

def pickle_code(co):
    if co.co_freevars or co.co_cellvars:
        #we can not do this safely
        print "OH NO code object unsafe"

    data=(
        co.co_argcount,
        co.co_nlocals,
        co.co_stacksize,
        co.co_flags,
        co.co_code,
        co.co_consts,
        co.co_names,
        co.co_varnames,
        co.co_filename,
        co.co_name,
        co.co_firstlineno,
        co.co_lnotab)

    return unpickle_code,data

# register with pickle the logic for handling
# code objects in pickle.
copy_reg.pickle(types.CodeType,pickle_code)


