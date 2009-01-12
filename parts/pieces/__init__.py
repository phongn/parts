import glob,os.path

objs=glob.glob(os.path.join(__path__[0],'*.py'))
for i in objs:
    name = os.path.splitext(os.path.basename(i))[0]
    if name != '__init__':
        locals()[name]=__import__(name,globals(),locals(),[])


