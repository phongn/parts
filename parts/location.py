'''
this file contains wrappers used by parts of SDK functions, should be safe to remove
should see about adding message saying to stop using these objects, so we can start
removing them.
'''

import os
import SCons.Script
import pattern
import common

class Bin:
    def __init__(self, env):
        '''The constructor'''
        self.env=env
        #Location.__init__(self,SCons.Script.Dir('#$OUT_BIN'),obj,sub_dir)    
    def __call__ (self, obj, sub_dir=''):
        return self.env.SdkBin(obj,sub_dir)
        
class Lib:
    def __init__(self, env):
        '''The constructor'''
        self.env=env
        #Location.__init__(self,SCons.Script.Dir('#$OUT_BIN'),obj,sub_dir)    
    def __call__ (self, obj, sub_dir=''):
        return self.env.SdkLib(obj,sub_dir)
        
class Include:
    def __init__(self, env):
        '''The constructor'''
        self.env=env
        #Location.__init__(self,SCons.Script.Dir('#$OUT_BIN'),obj,sub_dir)    
    def __call__ (self, obj, sub_dir=''):
        return self.env.SdkInclude(obj,sub_dir)


 

















