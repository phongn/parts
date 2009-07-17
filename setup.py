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
                
from distutils.core import setup
setup(name="parts",
      description="Extenstion module to SCons build system",
      author="Jason Kenny",
      author_email="jason.l.kenny@intel.com",
      version=parts_version._PARTS_VERSION,
      packages=['parts']+get_packages('./parts')

      )

from distutils.file_util import copy_file
copy_file('parts/parts.bat', sys.prefix)
copy_file('parts/parts', sys.prefix)
