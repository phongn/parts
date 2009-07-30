import glob,os.path
import parts.common as common

#The pieces directories to load
pt_dirs=common.get_site_directories('pieces')
# scan each directory and load all the pieces file
for d in pt_dirs:
    if os.path.exists(d):
        objs=glob.glob(os.path.join(d,'*.py'))
        for i in objs:
            name = os.path.splitext(os.path.basename(i))[0]
            if name != '__init__':
                common.load_module([d],name,'pieces')
                #locals()[name]=__import__(name,globals(),locals(),[])



