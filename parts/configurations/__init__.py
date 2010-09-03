import parts.load_module as load_module
import parts.reporter as reporter

def configuration(type):
    try:
        mod=load_module.load_module(
            load_module.get_site_directories('configurations'),type,'configtype')
    except ImportError:
        reporter.report_error('configuration "%s" was not found.'%type,show_stack=False)
    
