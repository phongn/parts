import sys,os
sys.path.append('./parts') 
import parts_version
import distutils.file_util

# Going forward I think this script is will be supporting only the install command. I make another script to make "install packages"
# the extra part-site directory does not work with most of the Command builders in dist_util
# this is one reason why I feel the move to a new set of scripts. Course the raw open source version will not care much
# but it would be nice to allow other user syncing there own repository copy a way to add there own overrides.

def get_packages(path):
    ret=[]
    for d in os.listdir(path):
        np=os.path.join(path,d)
        if os.path.isdir(np) and d !='.svn':
            tmp=np.replace('/','.')[2:]
            tmp=tmp.replace('\\','.')            
            ret.append(tmp)
            tmp= get_packages(np)
            if tmp!=[]:
                ret.extend(tmp)
    return ret

def get_data_files(root,path):
    ret=[]
    files=[]
    if os.path.exists(path) == False:
        return ret
    pth=os.path.join(root,path)
    for d in os.listdir(path):
        np=os.path.join(path,d)
        if os.path.isdir(np) and d.endswith('.svn')==False:
            tmp= get_data_files(root,np)
            if tmp!=[]:
                ret.extend(tmp)
        elif os.path.isfile(np) and d.endswith('.py'):
            files.append(np)
    if files != []:
        ret.append( (pth,files) )
    return ret

app_path=''

# global system area ..
if sys.platform == 'win32':
    syspath=os.environ['ALLUSERSPROFILE']
elif sys.platform == 'darwin':
    syspath='/Library/Application Support/parts'
else:
    syspath='/usr/share/parts'

# to allow install if root access is not used	
if os.path.exists(syspath) == False:
	try:
		os.makedirs(syspath)
	except:
		pass
		
if os.access(syspath,os.W_OK ) == False:
	syspath=os.path.join(os.path.expanduser('~'),'.parts-site')	
	
	
	
	
local_overrides=get_data_files(syspath,'.parts-site')
##print local_overrides
## 
###uninstall previous data
##if 'install' in sys.argv:
##    #remove the system overrides.. be smarter about it if we can    
##    for path,flst in local_overrides:
##        for f in flst:
##            tmp= os.path.join(path,os.path.split(f)[1])
##            if os.path.exists(tmp):
##                print "Removing:",tmp
##                os.remove(tmp)
##        print "Removing:",path
##        os.rmdir(path)
##        
##    # remove parts # just whack the whole directory
##print 
##    #distutils.dir_util.remove_tree()
                
from distutils.core import setup
setup(name="parts",
        description="Extension module to SCons build system",
        author="Jason Kenny",
        author_email="jason.l.kenny@intel.com",
        version=parts_version._PARTS_VERSION,
        packages=['parts']+get_packages('./parts'),
        scripts=['parts/parts.bat','parts/parts'],
        data_files=local_overrides
        )

