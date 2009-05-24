# defines tools chain mstool.
# this is ideally used with other tools such
# as the Intel compiler to setup need tool chains and
# version of compatibility needed


def cl_setup(env,ver): 
    env['MSVC_VERSION']=ver
    env['MSVS_VERSION']=ver

def resolve(env,version):
    
    func=lambda x : cl_setup(x,version)
    return [
                ('cl',func), # see if we can remove the CL compiler later??
                ('mslink',func),
                ('masm',func),
                ('mslib',func),
                ('midl',func)
            ]