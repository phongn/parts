
def gxx_setup(env,ver):
    env['GXX_VERSION']=ver
    env['GCC_VERSION']=ver

def resolve(env,version):
    func=lambda x : gxx_setup(x,version)

    host=env['HOST_PLATFORM']
    if host.OS=='darwin':
        return [
                ('g++',func),
                ('gcc',func),
                ('ar',None),
                ('gas',None),
                ('applelink',None)
            ]

    else:        
        return [
                ('g++',func),
                ('gcc',func),
                ('ar',None),
                ('gas',None),
                ('gnulink',None)
            ]
