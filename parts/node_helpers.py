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


class ninfotmp(object):
    def __init__(self):
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


class _AbsFile(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,path):
        return self.env.File(str(path),self.env['SRC_DIR']).srcnode().abspath

class _AbsDir(object):
    def __init__(self,env):
        self.env=env
    def __call__(self,path):
        return self.env.Dir(str(path),self.env['SRC_DIR']).srcnode().abspath

def AbsFile(env,path):
    tmp=env.File(str(path),env['SRC_DIR'])
    common.tag_node_ownership(env,tmp.Dir('.'))
    return tmp.srcnode().abspath

def AbsDir(env,path):
    tmp = env.Dir(str(path),env['SRC_DIR'])
    common.tag_node_ownership(env,tmp)
    return tmp.srcnode().abspath

# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

#add as global to part scope
api.register.add_global_parts_object('AbsFile',_AbsFile,True)
api.register.add_global_parts_object('AbsDir',_AbsDir,True)

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile=AbsFile
SConsEnvironment.AbsDir=AbsDir

