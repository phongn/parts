''' 
this file provides the AbsFile wrappers. I have not moved this to pieces area
yet as i need a way to safely add the global object to parts export statement
'''


class _AbsFile:
    def __init__(self,env):
        self.env=env
    def __call__(self,path):
        return self.env.File(str(path),self.env['SRC_DIR']).srcnode().abspath

class _AbsDir:
    def __init__(self,env):
        self.env=env
    def __call__(self,path):
        return self.env.Dir(str(path),self.env['SRC_DIR']).srcnode().abspath

def AbsFile(env,path):
    return env.File(str(path),env['SRC_DIR']).srcnode().abspath

def AbsDir(env,path):
    return env.Dir(str(path),env['SRC_DIR']).srcnode().abspath
    

# import the meta object we will need to add our code to as methods
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.AbsFile=AbsFile
SConsEnvironment.AbsDir=AbsDir