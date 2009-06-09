''' 
This contain the base code for all configurations we define in parts, and 
some helpfunction to help dump data, or get the correct configuration data
'''

import common
import version
import SCons.Script
import configurations,version

##def default_tool_add(map,tool,ver,config):
##    '''
##    This is the default tool add function used by the configuration objects.
##    It provides common basic functionality that shoudl be need by most common
##    tools.
##    '''
##    if ver==None:
##        map['tools']=[tool]
##    else:
##        map['tools']=[(tool,{'version':ver})] 
##    return True   
##
##def config_default_tool(map,tool,ver,config):
##    ''' 
##    This tries to get the default configuration based what Scons says is the default compiler.
##    We use this to get the best configurations setting to use.
##    '''
##    # try to see what the default env will be and set it up with predefined settings
##    # currently we just base this off the C compiler, in the future it should do more
##    cc=SCons.Script.DefaultEnvironment()['CC']
##    map.update( get_config(config,cc,ver) )
##    return True

def null_ver_mapper(env):
    return '0.0.0'

# this is an internal trick to make the configuration object look like a function
# but to have it instead store it self in a global map
g_configuration={}

def ConfigValues(**kw):
    return kw

class configuration:
    def __init__(self,default_ver_func,post_process_func=None):
        self.default_ver_func=default_ver_func
        self.post_process_func=post_process_func
        self.ver_rng={} 
        
    def map_none_version(self,env):
        return self.default_ver_func(env)
        
    def VersionRange(self,ver_rng,replace={},filter={},append={},prepend={},prepend_env={},append_env={},post_process_func=None):
        self.ver_rng[version.version_range(ver_rng)]={
        'append':append,
        'prepend':prepend,
        'replace':replace,
        'filter':filter,
        'append_env':append_env,
        'prepend_env':prepend_env,
        'post_process_func':post_process_func
        }
        
    def merge(self,ver,cfg):
        
        # need range to for store key later
        ver_rng=version.version_range()
        for v_range,val in self.ver_rng.iteritems():
            if ver in v_range:        
                mysetting=val
                ver_rng=v_range
                break
        else:
            return cfg,version.version_range()
        
        settings=cfg[0]
        settings_ex=cfg[1]
        
        # setup settings_ex
        tmp = mysetting['post_process_func']
        if settings_ex.has_key('post_process_func')==False:
            settings_ex['post_process_func']=[]
        if tmp is not None:
            settings_ex['post_process_func'].append(tmp)
        if self.post_process_func is not None:
            settings_ex['post_process_func'].append(self.post_process_func)
        
        settings_ex['default_ver_func']=[]
        if self.default_ver_func is not None: # should not be None.. clean up latter
            settings_ex['default_ver_func'].append(self.default_ver_func)
        
        tmp= mysetting['prepend_env']
        settings_ex['prepend_env']=[]
        if tmp!=None:
            settings_ex['prepend_env'].append(tmp)
            
        tmp= mysetting['append_env']
        settings_ex['append_env']=[]
        if tmp!=None:
            settings_ex['append_env'].append(tmp)
        
        #process normal flags settings
        # we process this in a for of:
        #{flag:{replace:val or [],append:[],prepend:[]}
        tmp= mysetting['replace']
        if tmp != {}:
            for k,v in tmp.iteritems():
                settings[k]={'replace':v,'append':[],'prepend':[]}
        
        tmp= mysetting['filter']        
        if tmp != {}:
            for k,v in tmp.iteritems():
                data=settings[k]
                for i in v:
                    for dk,dv in data.iteritems():
                        if i in dv:
                            dv.remove(i)
        
        tmp= mysetting['append']
        if tmp != {}:
            for k,v in tmp.iteritems():
                if settings.has_key(k)==False:
                    settings[k]={'append':[],'prepend':[]}
                settings[k]['append'].extend(v)
        
        tmp= mysetting['prepend']
        if tmp != {}:
            for k,v in tmp.iteritems():
                if settings.has_key(k)==False:
                    settings[k]={'append':[],'prepend':[]}
                settings[k]['prepend']=v.extend(settings[k]['prepend'])
        
        return (settings,settings_ex),ver_rng
        

class _ConfigurationSet:
    def __init__(self,name,dependsOn):
        self.name=name
        # add note if depends on is a list.. only support single base
        self.depends=dependsOn
        self.map={}
        

    def has_tool(self,tool):
        # if the key exists it has been loaded.. however the tool
        # may have a value of None
        return self.map.has_key(tool)
    
    def has_tool_cfg(self,tool,host,target):
        
        # first see if we have matching tool
        tool_config=self.map.get(tool,None)
        if tool_config==None:
            # no tool defined.. return None so master logic can fallback
            return False
        
        # next find the host
        host_config=tool_config.get(host,None)
        if host_config==None:
            #Don't have anything for this tool to configure
            return False
        
        # next we find the target
        target_config=host_config.get(target,None)
        if target_config==None:
            #Don't have anything for this tool to configure
            return False
        return True
    
    def Dependent(self):
        return self.depends
    
    def Name(self):
        return self.name
            
    def add_config_setting(self,tool,ver_rng,host,target,settings,ver_mapper):
        
        if tool in self.map:
            if host in self.map[tool]:
                if target in self.map[tool][host]:
                    if self.map[tool][host][target].has_key('versions'):
                        if ver_rng in self.map[tool][host][target]['version']:
                            self.map[tool][host][target]['versions'][ver_rng].update(settings)
                            self.map[tool][host][target]['default_ver_func']=ver_mapping
                        else:
                            self.map[tool][host][target]['versions'][ver_rng]=settings
                            self.map[tool][host][target]['default_ver_func']=ver_mapping
                    else:
                        self.map[tool][host][target].update({
                                        "default_ver_func":ver_mapper,
                                        "versions":{ver_rng:settings}
                                    })
                else:
                    self.map[tool][host].update({target:{
                                        "default_ver_func":ver_mapper,
                                        "versions":{ver_rng:settings}
                                    }})
            else:
                self.map[tool].update({host:{target:{
                                        "default_ver_func":ver_mapper,
                                        "versions":{ver_rng:settings}
                                    }}})
        else:           
            self.map[tool]={host:
                                {
                                target:
                                    {
                                        "default_ver_func":ver_mapper,
                                        "versions":{ver_rng:settings}
                                    }
                                }
                            }
        
    def get_config_setting(self,env,tool,ver,host,target):
        
        # first see if we have matching tool
        tool_config=self.map.get(tool,None)
        if tool_config==None:
            # no tool defined.. return None so master logic can fallback
            return None
        
        # next find the host
        host_config=tool_config.get(host,None)
        if host_config==None:
            #Don't have anything for this tool to configure
            return None
        
        # next we find the target
        target_config=host_config.get(target,None)
        if target_config==None:
            #Don't have anything for this tool to configure
            return None

        # next we get the version range list
        versions=target_config.get('versions',None)
        if versions == None:
            return None
        
        #map version if set to None to best value based on mapping function
        if ver==None:
            ver=target_config['default_ver_func'](env)
        # see if we have a match with the version.
        ver_config=None
        for v_range in versions.keys():
            if ver in v_range:
                ver_config=versions[v_range]
                break
        else:
            return None
        
        return ver_config
    
    def resolve_version(self,tool,host,target,env):
        # this shoudl be called be cause we check that such as config existed first
        tool_config=self.map.get(tool,None)
        return self.map[tool][host][target]['default_ver_func'](env)

def DefineConfiguration(name,dependsOn='default'):
    # add configuration
    if g_configuration.has_key(name):
        print "ConfigurationSet",name," already exists"
        # warning is it exists?
    #add dependance
    g_configuration[name]=_ConfigurationSet(name,dependsOn)

def load_cfg(name):
    # stop any loop/crashes that might happen if loading a None cfg
    if name==None:
        return
    # load the configuration meta information
    configurations.configuration(name)
    # make sure any dependent config is loaded as well
    dep=g_configuration[name].Dependent()
    
    if g_configuration.has_key(dep)==False and dep is not None:
    
        load_cfg(dep)

def make_name_list(tool,host,target):
    nl=[
    tool+"_"+host.OS+"-"+host.ARCH+"_"+target.OS+"-"+target.ARCH,
    tool+"_"+host.OS+"-"+host.ARCH+"_"+target.OS+"-"+'unknown',
    tool+"_"+host.OS+"-"+'unknown'+"_"+target.OS+"-"+target.ARCH,
    tool+"_"+host.OS+"-"+'unknown'+"_"+target.OS+"-"+'unknown',
    
    tool+"_"+host.OS+"-"+host.ARCH+"_"+'unknown'+"-"+target.ARCH,
    tool+"_"+host.OS+"-"+host.ARCH+"_"+'unknown'+"-"+'unknown',
    tool+"_"+host.OS+"-"+host.ARCH+"_"+'unknown',
    tool+"_"+host.OS+"-"+host.ARCH,
    tool+"_"+host.OS+"-"+'unknown'+"_"+'unknown'+"-"+target.ARCH,
    tool+"_"+host.OS+"-"+'unknown'+"_"+'unknown'+"-"+'unknown',
    tool+"_"+host.OS+"-"+'unknown'+"_"+'unknown',
    tool+"_"+host.OS+"-"+'unknown',
    
    tool+"_"+'unknown'+"-"+host.ARCH+"_"+target.OS+"-"+target.ARCH,
    tool+"_"+'unknown'+"-"+host.ARCH+"_"+target.OS+"-"+'unknown',
    tool+"_"+'unknown'+"-"+'unknown'+"_"+target.OS+"-"+target.ARCH,
    tool+"_"+'unknown'+"_"+target.OS+"-"+target.ARCH,
    tool+"_"+'unknown'+"-"+'unknown'+"_"+target.OS+"-"+'unknown',
    tool+"_"+'unknown'+"_"+target.OS+"-"+'unknown',
    
    tool+"_"+'unknown'+"-"+host.ARCH+'_'+'unknown'+"-"+target.ARCH,
    tool+"_"+'unknown'+"-"+host.ARCH+'_'+'unknown'+"-"+'unknown',
    tool+"_"+'unknown'+"-"+host.ARCH+'_'+'unknown',
    tool+"_"+'unknown'+"-"+host.ARCH,
    tool+"_"+'unknown'+"-"+'unknown'+'_'+'unknown'+"-"+target.ARCH,
    tool+"_"+'unknown'+'_'+'unknown'+"-"+target.ARCH,
    tool+"_"+'unknown'+"-"+'unknown'+'_'+'unknown'+"-"+'unknown',
    tool+'_unknown_unknown',
    tool+'_unknown',
    tool
    ]
    return nl

def make_name_dict(tool,host,target):
    nl={
    tool+"_"+host.OS+"-"+host.ARCH+"_"+target.OS+"-"+target.ARCH:
    (tool,host.OS,host.ARCH,target.OS,target.ARCH),
    tool+"_"+host.OS+"-"+host.ARCH+"_"+target.OS+"-"+'unknown':
    (tool,host.OS,host.ARCH,target.OS,None),
    tool+"_"+host.OS+"-"+'unknown'+"_"+target.OS+"-"+target.ARCH:
    (tool,host.OS,None,target.OS,target.ARCH),
    tool+"_"+host.OS+"-"+'unknown'+"_"+target.OS+"-"+'unknown':
    (tool,host.OS,None,target.OS,None),
    
    tool+"_"+host.OS+"-"+host.ARCH+"_"+'unknown'+"-"+target.ARCH:
    (tool,host.OS,host.ARCH,None,target.ARCH),
    tool+"_"+host.OS+"-"+host.ARCH+"_"+'unknown'+"-"+'unknown':
    (tool,host.OS,host.ARCH,None,None),
    tool+"_"+host.OS+"-"+host.ARCH+"_"+'unknown':
    (tool,host.OS,host.ARCH,None,None),
    tool+"_"+host.OS+"-"+host.ARCH:
    (tool,host.OS,host.ARCH,None,None),
    tool+"_"+host.OS+"-"+'unknown'+"_"+'unknown'+"-"+target.ARCH:
    (tool,host.OS,None,None,target.ARCH),
    tool+"_"+host.OS+"-"+'unknown'+"_"+'unknown'+"-"+'unknown':
    (tool,host.OS,None,None,None),
    tool+"_"+host.OS+"-"+'unknown'+"_"+'unknown':
    (tool,host.OS,None,None,None),
    tool+"_"+host.OS+"-"+'unknown':
    (tool,host.OS,None,None,None),
    
    tool+"_"+'unknown'+"-"+host.ARCH+"_"+target.OS+"-"+target.ARCH:
    (tool,None,host.ARCH,target.OS,target.ARCH),
    tool+"_"+'unknown'+"-"+host.ARCH+"_"+target.OS+"-"+'unknown':
    (tool,None,host.ARCH,target.OS,None),
    tool+"_"+'unknown'+"-"+'unknown'+"_"+target.OS+"-"+target.ARCH:
    (tool,None,None,target.OS,target.ARCH),
    tool+"_"+'unknown'+"_"+target.OS+"-"+target.ARCH:
    (tool,None,None,target.OS,target.ARCH),
    tool+"_"+'unknown'+"-"+'unknown'+"_"+target.OS+"-"+'unknown':
    (tool,None,None,target.OS,None),
    tool+"_"+'unknown'+"_"+target.OS+"-"+'unknown':
    (tool,None,None,target.OS,None),
    
    tool+"_"+'unknown'+"-"+host.ARCH+'_'+'unknown'+"-"+target.ARCH:
    (tool,None,host.ARCH,None,target.ARCH),
    tool+"_"+'unknown'+"-"+host.ARCH+'_'+'unknown'+"-"+'unknown':
    (tool,None,host.ARCH,None,None),
    tool+"_"+'unknown'+"-"+host.ARCH+'_'+'unknown':
    (tool,None,host.ARCH,None,None),
    tool+"_"+'unknown'+"-"+host.ARCH:
    (tool,None,host.ARCH,None,None),
    tool+"_"+'unknown'+"-"+'unknown'+'_'+'unknown'+"-"+target.ARCH:
    (tool,None,None,None,target.ARCH),
    tool+"_"+'unknown'+'_'+'unknown'+"-"+target.ARCH:
    (tool,None,None,None,target.ARCH),
    tool+"_"+'unknown'+"-"+'unknown'+'_'+'unknown'+"-"+'unknown':
    (tool,None,None,None,None),
    tool+'_unknown_unknown':
    (tool,None,None,None,None),
    tool+'_unknown':
    (tool,None,None,None,None),
    tool:
    (tool,None,None,None,None)
    }
    return nl




def load_tool_config(env,name,tool,host,target):
    
    ## First we need to start by loading base config
    # get dependent confg
    dep=g_configuration[name].Dependent()
    base_settings=({},{})
    base_ver_mapper=null_ver_mapper
    # do we have this config loaded already?
    if dep != None:
        if g_configuration[dep].has_tool_cfg(tool,host,target) == False:
            # if not load it
            load_tool_config(env,dep,tool,host,target)    

    ## Load our config data, and map the version value
    name_list=make_name_list(tool,host,target)
    found=True
    ver=None
    for k in name_list:
        try:
            
            mod=common.load_module('parts.configurations.'+name,k)
            print 'Configurtation [',name,'] loaded file:',k
            #Map version if unknown
            ver=mod.config.map_none_version(env)
            break
        except:
            pass
        
    else:
        #if dep == None:
        #    print 'Configurtation [',name,'] found no configruation for tool:',k
        found=False # nothing found

    ## Last we merge settings and store
    if dep != None:
        # Get base settings
        base_settings=g_configuration[dep].get_config_setting(env,tool,ver,host,target)
    
    if found==True:
        # merge setting
        settings,ver_rng=mod.config.merge(ver,base_settings)
        #print settings
        #store setting
        g_configuration[name].add_config_setting(tool,ver_rng,host,target,settings,mod.config.default_ver_func)
    else:
        g_configuration[name].add_config_setting(tool,version.version_range(),host,target,base_settings,base_ver_mapper)

def get_config(env,name,tool,host,target):
    # is "meta" config loaded
    if g_configuration.has_key(name)==False:
        #if not load it
        load_cfg(name)
    config=g_configuration[name]
    # is tool loaded?
    ver=None
    if config.has_tool_cfg(tool,host,target)==False:    
    #if not load it
        ver=load_tool_config(env,name,tool,host,target)
    # if version is None get a real version
    if ver==None:
        ver=config.resolve_version(tool,host,target,env)
    # get settings    
    settings=config.get_config_setting(env,tool,ver,host,target)
    if settings==None:
        return ({},{})
    return settings
    
def apply_config(env,name=None,host=None,target=None):
    # get tools set to configure
    tools=env['CONFIGURED_TOOLS']
    #print "Configured Tool to get configuration from",tools
    host=env['HOST_PLATFORM']
    target=env['TARGET_PLATFORM']
    if name==None:
        env['CONFIG']=env.subst('${CONFIG}')
        name=env['CONFIG']
        
    print "Applying configuration:",name
    #print "tools that have been configured",tools
    for t in tools:
        settings,setting_extra=get_config(env,name,t,host,target)
        #print t,settings,setting_extra
        for flag,items in settings.iteritems():
            
            # replace values
            if items.has_key('replace'):
                env.Replace(**{flag:items['replace']})
            if items.has_key('append'):
                env.Append(**{flag:items['append']})
            #prepend values in env
            if items.has_key('prepend'):
                env.Prepend(**{flag:items['prepend']})
            
        tmp=setting_extra.get('prepend_env',{})
        for i in tmp:
            for k,v in i.iteritems():
                env.PrependENVPath(k,v)
        
        tmp=setting_extra.get('append_env',{})
        for i in tmp:
            for k,v in i.iteritems():
                env.AppendENVPath(k,v)
        
        tmp=setting_extra.get('post_process_func',[])
        for f in tmp:
            f(env)
                
def _isconfigbasedon(env,name,config):                
    tmp=g_configuration[config]
    if tmp.Name() == name:
        return True
    if tmp.Dependent() is not None:
        return _isconfigbasedon(env,name,tmp.Dependent())
    else:
        return False
    
def isConfigBasedOn(env,name):
    config=env['CONFIG']
    return _isconfigbasedon(env,name,config)
            
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.isConfigBasedOn=isConfigBasedOn
        
common.AddVariable(['CONFIG','config'],'${default_config}','The configuration to use')
common.AddVariable('default_config','debug','The configuration to use by default')

