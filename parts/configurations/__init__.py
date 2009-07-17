

def configuration(type):
    import parts.common as common
    import os
    mod=common.load_module(
        common.get_site_directories('configurations'),type,'configtype')
    
