import os
import re
import sys
import SCons.Script
import SCons.Builder


import parts.api as api
import parts.api.output as output

def scanFile(env,infile, outfile):
    lineno = 0       # line number
    sfile = "" + str(infile)
    outputf = file(outfile.abspath, 'w');
    inputf = file(infile.abspath)
    
    for line in inputf:
        lineno +=  1
        
        if lineno == 1:
            outputf.writelines(env.XmlHeader +'\n')           
        line = line.rstrip()        
        outputf.write(line+'\n')           

def addXmlHeader(target, source, env):
    
    for outfile, infile in zip(target,source):                                                  
        lineno = 0       # line number
        outputf = file(outfile.abspath, 'w');
        inputf = file(infile.abspath)
        
        for line in inputf:           
            if lineno == 1:
                outputf.writelines(env.XmlHeader +'\n')           
            line = line.rstrip()        
            outputf.write(line+'\n') 
            lineno +=  1
            
    return 0

def addXmlHeader_emitter(target, source, env):
    output=[]
    if len(target) != 1:
        api.output.error_msg("Only one input is allowed")
    
    try:
        dnodes = env.arg2nodes(target, env.fs.Dir)
    except TypeError:
        api.output.error_msg("Target `%s' is a file, but should be a directory.  Perhaps you have the arguments backwards?" % str(dir))
    
    for s in source:
        path,base=os.path.split(s.path)
        output.append(env.File(base,target[0]))    
    return (output, source)

api.register.add_builder('__AddXmlHeader__',SCons.Script.Builder(
        action=SCons.Script.Action(addXmlHeader),  
        emitter=addXmlHeader_emitter,
        target_factory=SCons.Node.FS.Entry
        ))

    
def AddXmlHeader(env,target, source,sub_dir = '.',**kw):
    if sub_dir is not '.':
        tmp_target = os.path.join(target,sub_dir)
    else:
        tmp_target = target    
    return env.__AddXmlHeader__(tmp_target,source,**kw)

def AddXmlHeaderAs(env,target,source,**kw):
    output = []
    for target_i,source_i in zip(target,source):
        target_path = os.path.split(str(target_i))[0]
        output += AddXmlHeader(env,target_path,source_i)
    return output
        
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object  
SConsEnvironment.AddXmlHeader=AddXmlHeader        
SConsEnvironment.AddXmlHeaderAs=AddXmlHeaderAs