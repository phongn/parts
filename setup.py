import sys 
sys.path.append('./parts') 
import parts_version

from distutils.core import setup
setup(name="parts",
      description="Extenstion module to SCons build system",
      author="Jason Kenny",
      author_email="jason.l.kenny@intel.com",
      version=parts_version._PARTS_VERSION,
      packages=['parts','parts.configurations','parts.tools','parts.pieces']

      )

from distutils.file_util import copy_file
copy_file('parts/parts.bat', sys.prefix)
copy_file('parts/parts', sys.prefix)
