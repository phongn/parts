
# defines tools chain for the general Gnu set( as needed for Intel Compiler posix or simular tools)

def _setup(env,ver):
    env['GXX_VERSION']=ver
    env['GCC_VERSION']=ver

def resolve(env,version):
    func=lambda x : _setup(x,version)
    return [
                ('g++',func),
                ('gcc',func),
                ('ar',None),
                ('gnulink',None),
        ]



