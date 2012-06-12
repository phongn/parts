
import imp
import os

def find_tests():
    ret=[]
    for root, dirs, files in os.walk('.'):
        #print 'Searching for tests in:', root
        if '.svn' in dirs:
            dirs.remove('.svn')
        for f in files:
            if f.endswith('.test.py'):
                print 'Loading tests from module', f,
                try:
                    ret.append(my_load(root,f[:-3]))
                    print "- Succeeded!"
                except Exception,ec:
                    import traceback
                    print "- Failed! "
                    print "Stack Dump-------------------------------------------- "
                    traceback.print_exc()
                    print "Stack Dump - End --------------------------------------"
    return ret
                    
                
def my_load(path,name):    
    fp, pathname, description = imp.find_module(name,[path])
    try:
        return imp.load_module(name[:-5], fp, pathname, description)
    finally:
        # Since we may exit via an exception, close fp explicitly.
        if fp:
            fp.close()
    return None
