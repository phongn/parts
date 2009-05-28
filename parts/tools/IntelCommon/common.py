
from parts.tools.Common.ToolSetting import ToolSetting
from parts.tools.Common.ToolInfo import ToolInfo
from parts.version import version_range

intel_9='([9])([0-1])'
intel_10='([0-9][0])([0-9]).([0-9][0-9][0-9])'
intel_11='([0-9][1])([0-9]).([0-9][0-9][0-9])'
#different layout in registry
intel_11_1='[0-9][0-9][0-9]'



class IntelcInfo(ToolInfo):
    def __init__(self,version,install_scanner,script,subst_vars,shell_vars,test_file):
        ToolInfo.__init__(self,version,install_scanner,script,subst_vars,shell_vars,test_file)
        self.version=version_range(version)
    
    def version_set(self):
        return self.version


Intelc=ToolSetting('INTELC')

