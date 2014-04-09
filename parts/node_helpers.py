'''
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''

import glb
import common
import api.output
import metatag
import ctypes
import exceptions

import SCons.Script
import SCons.Util
import SCons.Node.FS

import os

from SCons.Debug import logInstanceCreation

class ninfotmp(object):
    def __init__(self):
        if __debug__: logInstanceCreation(self)
        self.timestamp=0
        self.csig=0

def node_up_to_date(node):
    '''
    Expects a SCons node object, will test against stored info
    to see if it is uptodate
    '''

    if isinstance(node,SCons.Node.Node):
        node.disambiguate()
        dbentry=node.get_stored_info()
        ninfo=dbentry.ninfo

    elif common.is_string(node):
        node=glb.engine.def_env.Entry(node)
        node.disambiguate()
        tmp=metatag.MetaTagValue(node,'uptodate','parts',None)
        if tmp is True:
            return True
        elif tmp is None:
            pass
        else:
            api.output.verbose_msg("update_check",tmp)
            return False
        dbentry=node.get_stored_info()
        ninfo=dbentry.ninfo

    else:

        ninfo=ninfotmp()
        ninfo.timestamp=node['timestamp']
        ninfo.csig=node['csig']

        node=glb.engine.def_env.Entry(node['name'])
        node.disambiguate()
        tmp=metatag.MetaTagValue(node,'uptodate','parts',None)
        if tmp is True:
            return True
        elif tmp is None:
            pass
        else:
            api.output.verbose_msg("update_check",tmp)
            return False




    # see if node time stamp matches
    tmp=getattr(ninfo,'timestamp',None)
    if tmp is None:
        s="'%s' does not exist in the SCons DB"%(node)
        metatag.MetaTag(node,ns='parts',uptodate=s)
        api.output.verbose_msg("update_check",s)
        return False
    if node.exists() == False:
        s="'%s' does not exist"%(node)
        metatag.MetaTag(node,ns='parts',uptodate=s)
        api.output.verbose_msg("update_check",s)
        return False
    if node.get_timestamp() != tmp:
        # timestamp did not match.. try md5
        api.output.verbose_msg("update_check","TimeStamp diff in '%s'"%(node))
        if node.get_csig() != getattr(ninfo,'csig',0):
            # md5 failure
            #print ninfo.__dict__,node.get_csig()
            s="%s is out of date because of differences"%(node)
            metatag.MetaTag(node,ns='parts',uptodate=s)
            api.output.verbose_msg("update_check",s)
            return False
    #api.output.verbose_msg("update_check","%s seems to be unmodified"%(node))
    metatag.MetaTag(node,ns='parts',uptodate=True)
    return True

def abs_path(env, path, create_node, need_tag = True):
    path = env.subst(path)
    if path.startswith('#'):
        directory = env.Dir('#')
        path = path[len('#'):]
    else:
        directory = env.Dir(env['SRC_DIR'])
    result = create_node(path, directory)
    if need_tag:
        common.tag_node_ownership(env, result.dir)
    return result.srcnode().abspath


class _AbsFile(object):
    def __init__(self,env):
        if __debug__: logInstanceCreation(self)
        self.env=env
    def __call__(self, path):
        return abs_path(self.env, path, self.env.File, False)

class _AbsDir(object):
    def __init__(self,env):
        if __debug__: logInstanceCreation(self)
        self.env=env
    def __call__(self,path):
        return abs_path(self.env, path, self.env.Dir, False)

def AbsFile(env, path):
    return abs_path(env, path, env.File)

def AbsDir(env, path):
    return abs_path(env, path, env.Dir)

# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

#add as global to part scope
api.register.add_global_parts_object('AbsFile',_AbsFile,True)
api.register.add_global_parts_object('AbsDir',_AbsDir,True)

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile=AbsFile
SConsEnvironment.AbsDir=AbsDir

