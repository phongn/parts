
import common
import ToolChain
import SCons.Tool

def get_tlset_module(tlchain,version):
    # first try to load exact match.. then general match
    if version:
        name_list=[tlchain+"_"+version,tlchain]
    else:
        name_list=[tlchain]
    for k in name_list:
        try:
            mod=common.load_module('parts.ToolChain',k)
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
    new_list=[]
    repeat=False
    for t in tlset:
        # test if tool has been seen to prevent loops
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