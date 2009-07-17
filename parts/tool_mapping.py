
import common
import SCons.Tool
import os

def get_tlset_module(tlchain,version):
    # first try to load exact match.. then general match
    if version:
        name_list=[tlchain+"_"+version,tlchain]
    else:
        name_list=[tlchain]
    for k in name_list:
        try:
            mod=common.load_module(common.get_site_directories('toolchain'),k,'toolchain')
            #print 'Found ToolChain:',k
            return mod
        except:
            pass
        
    #print "Tool Chain not found:",tlchain
    return None

def get_tools(env,tlset):
    
    # for each tool see if the value is a tool, or abstaction
    # this is done via testing is a tool exist with that name
    # this is to prevent loops like cl->msvc->cl->msvc etc...
    # ("name",None) -> tool chain
    # ("name","val") -> tool chain
    # ("name",{}) ->tool
    # ("name",functor) ->tool
    
    new_list=[]
    repeat=False
    for t in tlset:
        if t[1] == None or common.is_string(t[1]):
            #get the list subst for the value
            repeat=True
            mod=get_tlset_module(t[0],t[1])
            # check to see if loaded a chain mapping
            if mod:
                new_list.extend(mod.resolve(env,t[1]))
            else:
                # see if this is a tool that is loadable
                try:
                    SCons.Tool.Tool(t[0],toolpath=env['toolpath'])
                    new_list.extend([(t[0],{})])
                except:
                    print "Unknown ToolChain or Tool:",t[0]
                    pass
        else:
            #This has been handled
            new_list.append(t)
    
    if repeat:
        return get_tools(env,new_list)
    # returns in the end [(tool_str,{of what to apply first} or functor(env)),...]
    return new_list

def _ToolChain(env,chainlist):
    ## resolve tool chain into the list of tools to setup
    # normalize for of all tools requested
    tlset=common.process_tool_arg(chainlist)
    # get the list
    tool_list=get_tools(env,tlset)
    
    ##add tools
    if not env.has_key('CONFIGURED_TOOLS'):
        env['CONFIGURED_TOOLS']=[]
    for t in tool_list:
        # apply pre tool configurtation part so the tool will setup correctly
        if t[1]==None:
            pass
        elif common.is_dictionary(t[1]):
            env.Replace(**t[1])
        else:
            t[1](env)
            
        # apply the tool to the enviroment
        env['CONFIGURED_TOOLS'].append(t[0])
        env.Tool(t[0])
        
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object

SConsEnvironment.ToolChain=_ToolChain
