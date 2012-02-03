
# defines tools chain for the general Gnu set( as needed for Intel Compiler posix or simular tools)

def _setup(env,ver):
    env['GXX_VERSION']=ver
    env['GCC_VERSION']=ver

def resolve(env,version):
    func=lambda x : _setup(x,version)
    host=env['HOST_PLATFORM']
    if host.OS=='darwin':
        return [
                ('g++',func,False),
                ('gcc',func,False),
                ('ar',None),
                ('gas',None),
                ('applelink',None)
            ]

    else:        
        return [
                ('g++',func,False),
                ('gcc',func,False),
                ('ar',None),
                ('gas',None),
                ('gnulink',None)
            ]



