''' 
This contain the base code for all configurations we define in parts, and 
some helpfunction to help dump data, or get the correct configuration data
'''

import common
import version
import SCons.Script

def default_tool_add(map,tool,ver,config):
    '''
    This is the default tool add function used by the configuration objects.
    It provides common basic functionality that shoudl be need by most common
    tools.
    '''
    if ver==None:
        map['tools']=[tool]
    else:
        map['tools']=[(tool,{'version':ver})] 
    return True   

def config_default_tool(map,tool,ver,config):
    ''' 
    This tries to get the default configuration based what Scons says is the default compiler.
    We use this to get the best configurations setting to use.
    '''
    # try to see what the default env will be and set it up with predefined settings
    # currently we just base this off the C compiler, in the future it should do more
    cc=SCons.Script.DefaultEnvironment()['CC']
    map.update( get_config(config,cc,ver) )
    return True

# this is an internal trick to make the configuration object look like a function
# but to have it instead store it self in a global map
g_configuration={}

class configuration:
    '''
    This object store the data needed for a given configuration. 
    Storage key for a configuration are currently the name ( config is better 
    as this is release or debug), version and tool name ( as in icl or cl)

    The config function is used to delay load needed data so differet tools
    can better set values as verify if otehr type of tools are being used that 
    might require different behavor, for example icl and mscrt do this.    
    '''
    def __init__(self,name,tool,ver=None,add_tool_func=default_tool_add,**kw):
        self.name=name
        self.tool=tool
        self.ver=ver
        self.cfg_map=kw
        
        self.config_func=add_tool_func
        
        if self.tool in g_configuration:
            if self.ver in g_configuration[self.tool]:
                g_configuration[self.tool][self.ver].update({self.name:self})
            else:
                g_configuration[self.tool].update({self.ver:{self.name:self}})
        else:
            g_configuration[self.tool]={self.ver:{self.name:self}}
            
    def config_map(self,ver=None):
        def_env=SCons.Script.DefaultEnvironment()
        rpt=def_env['PARTS_REPORTER']
        if ver==None:
            use_ver=self.ver
        else:
            use_ver=ver
        if self.config_func(self.cfg_map,self.tool,use_ver,self.name) == False:
            rpt.part_warning(None,'Configuration '+str(self.name)+' '+str(self.tool)+' '+str(self.ver)+' failed to correctly config itself.')
            #print '\n********************************************************************'
            #print 'PARTS: Warning -- Configuration',self.name,self.tool,self.ver,'failed to correctly config itself.'
            #print '********************************************************************\n'
        #print "----",self.tool,self.name,self.cfg_map
        return self.cfg_map


def get_config(config,tool,ver=None):
    ''' this function will return a requested configuration. If it can't find it, 
    it shoudl fallback in a graceful fashion. There maybe cases still in which new 
    configuration are added that could cause an inifite loop to happen. But i believe it 
    should only happen because of a mistake in the configuration setup.
    '''
    ##print 'Getting config =',config,tool,ver
    org_ver=ver
    # first we verfiy what we have
    # do we have this tool?
    if g_configuration.has_key(tool)==True:
        has_tool=True
        has_ver=False # this is just setup for later
        #do we have this versions?
        ver_list=g_configuration[tool]
        lst= ver_list.keys()
        lst.sort(lambda a,b: common.CompareVersionNumbers(b,a))
        v=common.get_version_from_list(ver,lst)
        if v != False:
            #print "Match found with",ver,'in',v
            ver=v
            has_ver=True # this is the case
            #do we have this config?
            if ver_list[v].has_key(config)==True:
                has_config=True
            else:
                has_config=False
            
        else :
            #do we have this config?
            if g_configuration[tool][None].has_key(config)==True:
                has_config=True
            else:
                has_config=False
                
    else:
        has_tool=False
        has_ver=False
        has_config=False 
    ##print has_tool,has_ver,has_config
    def_env=SCons.Script.DefaultEnvironment()
    rpt=def_env['PARTS_REPORTER']
    if has_tool==True and has_ver==True and has_config==True: 
        cfg=g_configuration[tool][ver][config]
        ##print 'Got config =',config,tool,ver
        if org_ver!=ver and len(org_ver)>len(ver):
            #print 'Got config a=',config,tool,org_ver
            return cfg.config_map(org_ver)
        else:
            #print 'Got config b=',config,tool,ver
            return cfg.config_map()
    elif has_tool==False:
        rpt.part_warning(None,'Unknown Tool ['+str(tool)+'] Trying defaults tools with config='+config)
        #print '\n********************************************************************'
        #print 'PARTS: Warning -- Unknown Tool [',tool,'] Trying defaults tools with config='+config
        #print '********************************************************************\n'
        return get_config(config,'default')
    if has_tool==True and has_ver==True and has_config==False: 
        if g_configuration[tool][ver].has_key('default'):
            return get_config('default',tool,ver)
        else:
            configtmp=g_configuration[tool][ver].keys()[0]
            #print '\n********************************************************************'
            rpt.part_warning(None,'Config ['+str(config)+'] not found for tool ['+str(tool)+\
            ']. looked for config=default\nBut Config [ default ] not found for tool ['+str(tool)+'].  Trying config='+str(configtmp))
            #print 'PARTS: Warning -- Config [',config,'] not found for tool [',tool,']. looked for config=default'
            #print '       But Config [ default ] not found for tool [',tool,'].  Trying config='+configtmp
            #print '********************************************************************\n'
            return get_config(configtmp,tool)
    if has_tool==True and has_ver==False and has_config==True: # we have a None version
        rpt.part_warning(None,'version ['+str(ver)+'] not found for tool,config ['+str(tool)+','+str(config)+'].  Trying version=None(default).')
        #print '\n********************************************************************'
        #print 'PARTS: Warning -- version [',ver,'] not found for tool,config [',tool,',',config,'].  Trying version=None(default).'
        #print '********************************************************************\n'
        return get_config(config,tool)
    if has_tool==True and has_ver==False and has_config==False: # we don't have a None version 
        rpt.part_warning(None,'version ['+str(ver)+'] not found, Tools does not define default version\n       Using Defaults')
        #print '\n********************************************************************'
        #print 'PARTS: Warning -- version [',ver,'] not found, Tools does not define default version'
        #print '       Using Defaults'
        #print '********************************************************************\n'
        return get_config('default','default')

def dump_config_list(tool=None):
    '''
    prints out what configuration have been defined, allow one to filter configurations
    by the name of the tool. If the tools is empty it will print the whole tree.
    '''
    print '\n********************************************************************'
    print 'Known configurations\n'
    
    for tl in g_configuration:
        if tool==None or tool==tl:
            print tl
            for ver in g_configuration[tl]:
                print '\t',ver
                for cfg2 in g_configuration[tl][ver]:
                    print '\t\t',cfg2
    print '********************************************************************\n'
                    
