''' 
this code is called by SCons to work around a "bug" with the scanner in how it uses the subst() API
The primary issue is that scanner often try to get a list value based variable it wants to expand, 
because the subst code at the moment does not allow for an item to expand it no more than one item, it 
gets back some string like "foo.a boo.a" not "foo.a" and "boo.a" which means that scanner will fail to find
the item it is scanning for and fail to set a dependancy as needed. Since Parts requires the need for the 
subst to posilbly process more than one item, and the currently the scanner tend to subst() each item in 
the list seperatly, we "pre expand the values" to allow the scanner to work as expected. This also give us a small
speed boost as we fill in the values as at this point it is not going to change. This prevents extra subst() 
processing later on the same environment for the same variable.
'''

import SCons.Tool
import SCons.Scanner
from .. import mappers
import thread

## this deal with issue with the program scanner for stuff that has .a/.lib./dylib/.so files
#scons_scan=SCons.Scanner.Prog.scan

#def pscan(node, env, libpath = ()):
#    print env.get('LIBS')
#    env.subst("$LIBS")
#    return scons_scan(node,env,libpath)

#kw={}
#kw['path_function'] = SCons.Scanner.FindPathDirs('LIBPATH')
#SCons.Tool.ProgramScanner=SCons.Scanner.Base(pscan, "ProgramScanner", **kw)

# this get the general cases ( for example with handle libpath for the program scanner case above)
class PartPathDirsWrapper(object):
    
    def __init__(self, obj):
        self.obj = obj

    def __call__(self, env, dir, target=None, source=None, argument=None):

        prop_lst=env.get(self.obj.variable,[])
        if prop_lst!=[]:
            #print prop_lst
            ret=mappers.sub_lst(env,prop_lst,thread.get_ident(),recurse=False)
            #env[self.obj.variable]=ret'''
            #print 1,env[self.obj.variable]
        return self.obj(env,dir,target,source,argument)


def Scanner_override():
    ## this is for fixing an issue with the scanners in which one item in a env
    ## does not have the $vars fully expanded, which causes an issue with in the
    ## dependency tree. This leads to a false rebuild of few files
    for k in SCons.Tool.SourceFileScanner.function.keys():
        if isinstance(SCons.Tool.SourceFileScanner.function[k].path_function,SCons.Scanner.FindPathDirs):
            SCons.Tool.SourceFileScanner.function[k].path_function=PartPathDirsWrapper(
            SCons.Tool.SourceFileScanner.function[k].path_function)

            


    