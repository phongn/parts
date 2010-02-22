import parts.load_module as load_module

def configuration(type):
    mod=load_module.load_module(
        load_module.get_site_directories('configurations'),type,'configtype')
    
