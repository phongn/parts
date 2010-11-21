
from .. import common
from .. import reporter

def AddArchitecture(arch_alias,arch = '', change_arch_map = False):    
    if arch == '':
        arch = arch_alias
    if (arch_alias in common.g_arch_map) and (not change_arch_map): 
        reporter.report_warning(os_alias,"already exists as a Valid Platform\n  To force a change use AddArchitecture(arch_alias,arch,True)")
    else:
        common.g_arch_map[arch_alias] = arch 
    common.UpdateValidArchList()
        

def AddOS(os_alias,os = '', change_os_map = False):
    if os == '':
        os = os_alias
    if (os_alias in common.g_os_map) and (not change_os_map): 
        reporter.report_warning(os_alias,"already exists as a Valid Platform\n  To force a change use AddOS(os_alias,os,True)")
    else:
        common.g_os_map[os_alias] = os 
    common.UpdateValidOSList()
