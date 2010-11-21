
import SCons.Node.FS
import cPickle
import copy_reg
import types

def pickle_node(node):
    '''pickles a node object into a form we can use to have SCons remake the node again'''
    if isinstance(node,SCons.Node.FS.File):
        ntype='File'
        value=node.abspath
    elif isinstance(node,SCons.Node.FS.Dir):
        ntype='Dir'
        value=node.abspath
    elif isinstance(node,SCons.Node.FS.Entry):        
        ntype='Entry'
        value=node.abspath
    elif isinstance(node,SCons.Node.Python.Value):
        ntype='Value'
        value=str(node)
    else:
        return None
    #Parts#NODE:    
    return "{0}:{1}".format(ntype,value)
    
def unpickle_node(node):
    ''' recreate a node object.. hopefully mapped to an existing object in SCons FS manager'''
    ntype,value=node.split(":")
    
    if ntype=='File':
        return SCons.Node.FS.File(value)
    elif ntype=='Dir':
        return SCons.Node.FS.Dir(value)
    elif ntype=='Entry':        
        return SCons.Node.FS.Entry(value)
    elif ntype=='Value':
        return SCons.Node.Python.Value(value)
    else:
        raise cPickle.UnpicklingError, 'Unknown Node Type {0}'.format(value)

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
        tmp=persid[len('Parts@FunctionType@'):]
        return unpickle_node(tmp)
    elif persid.startswith('Parts@FunctionType@'):
        tmp=persid[len('Parts@FunctionType@'):]
        return unpickle_function(tmp)
    else:
        raise pickle.UnpicklingError, 'Invalid persistent id'

## this code allow use to handle the pickle of byte code
## the other way we can do this is to use a libray 
## to grab the source code, given that we woudl always have 
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
 


