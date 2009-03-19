# defines tools chain cl ( as in microsft CL)


def cl_setup(env,ver):
    
    env['MSVC_VERSION']=ver
    env['MSVS_VERSION']=ver

def resolve(env,version):
    
    func=lambda x : cl_setup(x,version)
    return [
                ('cl',func),
                ('mslink',func),
                ('masm',func),
                ('mslib',func),
                ('midl',func)
            ]