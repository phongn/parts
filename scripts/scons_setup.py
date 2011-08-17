import os
import sys

def find_in_path(file):

    # get the path as a list
    pathlist = os.environ['PATH'].split(os.pathsep)

    # for each directory in the path list
    for dir in pathlist:
        filename = os.path.join(dir, file)
        # see if the file exists
        if os.path.isfile(filename):
            return dir
    return None


def scons_path(version=None):
    # fill in version logic later
    path=find_in_path('scons.py')
    if path is None:
        print "scons.py not found in path"
        return None
    sys.path = [path] + sys.path
    import scons


        

            
    
