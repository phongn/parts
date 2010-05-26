import sys,os
sys.path.append('./parts') 
import parts_version
import distutils.file_util
from distutils.command.install import install

class custom_install(install):
    def run(self):
        self.uninstall = os.path.join(self.install_scripts, "%s_uninstall.py" % self.distribution.get_name())
        
        if os.path.exists(self.uninstall):
            print "Uninstalling previous version"
            if self.dry_run:
                os.system("python %s -n" % self.uninstall)
            else:
                os.system("python %s" % self.uninstall)
        
        keep_record = True
        if not self.record:
            self.record = "install_record.txt"
            keep_record = False
        
        self.force = 1
        install.run(self)
        
        if not self.dry_run:
            self._generate_uninstall()
        
        if not keep_record:
            print "Removing unwanted record %s" % self.record
            if not self.dry_run: os.remove(self.record)
            self.record = None
    
    def _generate_uninstall(self):
        print "Generating uninstall script in %s" % self.uninstall
        out = open(self.uninstall, 'w')
        out.write("#!/usr/bin/env python\n")
        out.write("import os, sys\n\n")
        out.write("files = [\n")
        fin = open(self.record, 'r')
        for line in fin:
            line = line.strip();
            line = line.replace('\\', "\\\\");
            out.write("'%s',\n" % line)
        
        fin.close()
        out.write("__file__\n")
        out.write("]\n\n")
        out.write("dry_run = False\n")
        out.write("for arg in sys.argv:\n")
        out.write("\tif arg == '-n':\n")
        out.write("\t\tdry_run = True\n\n")
        
        out.write("for f in files:\n")
        out.write("\tif os.path.exists(f):\n")
        out.write("\t\tprint \"Removing %s\" % f\n")
        out.write("\t\tif not dry_run: os.remove(f)\n")
        
        out.write("\tf = f + 'c'\n")
        out.write("\tif os.path.exists(f):\n")
        out.write("\t\tprint \"Removing %s\" % f\n")
        out.write("\t\tif not dry_run: os.remove(f)\n")
        
        out.write("\tdir = os.path.dirname(f)\n")
        out.write("\ttry:\n")
        out.write("\t\twhile not dry_run:\n")
        out.write("\t\t\tos.rmdir(dir)\n")
        out.write("\t\t\tprint \"Removing %s\" % dir\n")
        out.write("\t\t\tdir = os.path.dirname(dir)\n")
        out.write("\texcept OSError:\n")
        out.write("\t\tpass\n")
        out.close()

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

def get_data_files(root,path,installpath):
    ret=[]
    files=[]
    if os.path.exists(path) == False:
        return ret
    pth=os.path.join(root,installpath)
    for d in os.listdir(path):
        np=os.path.join(path,d)
        if os.path.isdir(np) and d.endswith('.svn')==False:
            tmp= get_data_files(root,np,os.path.join(installpath,d))
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
    syspath=os.path.join(os.path.expanduser('~'))
    local_overrides=get_data_files(syspath,'.parts-site','.parts-site')
else:
    local_overrides=get_data_files(syspath,'.parts-site','parts-site')
    

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
        cmdclass={'install':custom_install},
        data_files=local_overrides
        )

