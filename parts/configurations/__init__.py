import parts.config
import glob,os.path

#define configs
parts.config.configuration('debug','default',None,parts.config.config_default_tool)
parts.config.configuration('release','default',None,parts.config.config_default_tool)
parts.config.configuration('default','default',None,parts.config.config_default_tool)

objs=glob.glob(os.path.join(__path__[0],'*.py'))

for i in objs:
    name = os.path.splitext(os.path.basename(i))[0]
    if name != '__init__':
        locals()[name]=__import__(name,globals(),locals(),[])
