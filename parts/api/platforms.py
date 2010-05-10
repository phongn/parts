
import parts.common
import parts.reporter

def AddArchitecture(arch_alias,arch = '', change_arch_map = False):    
    if arch == '':
        arch = arch_alias
    if (arch_alias in parts.common.g_arch_map) and (not change_arch_map): 
        parts.reporter.report_warning(os_alias,"already exists as a Valid Platform\n  To force a change use AddArchitecture(arch_alias,arch,True)")
    else:
        parts.common.g_arch_map[arch_alias] = arch 
    parts.common.UpdateValidArchList()
        

def AddOS(os_alias,os = '', change_os_map = False):
    if os == '':
        os = os_alias
    if (os_alias in parts.common.g_os_map) and (not change_os_map): 
        parts.reporter.report_warning(os_alias,"already exists as a Valid Platform\n  To force a change use AddOS(os_alias,os,True)")
    else:
        parts.common.g_os_map[os_alias] = os 
    parts.common.UpdateValidOSList()
