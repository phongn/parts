import sys,os
sys.path.append('./parts') 
import parts_version

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
		elif os.path.isfile(np):
			files.append(np)
	if file != []:
		ret.append( (pth,files) )
	return ret

app_path=''

# global system area
if sys.platform == 'win32':
    syspath=os.environ['ALLUSERSPROFILE']
elif host_os == 'darwin':
    syspath='/Library/Application Support/parts'
else:
    syspath='/usr/share/parts'

print get_data_files(syspath,'parts-site')
                
from distutils.core import setup
setup(name="parts",
        description="Extension module to SCons build system",
        author="Jason Kenny",
        author_email="jason.l.kenny@intel.com",
        version=parts_version._PARTS_VERSION,
        packages=['parts']+get_packages('./parts'),
        scripts=['parts/parts.bat','parts/parts'],
        data_files=get_data_files(syspath,'parts-site')
        )

