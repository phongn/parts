

def configuration(type):
    import parts.common as common
    mod=common.load_module('parts.configurations',type)
