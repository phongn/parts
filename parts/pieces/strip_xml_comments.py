import os
import re
import sys
import SCons.Script

import parts.api as api
import parts.api.output as output

xmlComment = re.compile(r'(.*)(<!--)(.*)(-->)(.*)')

commentStart = re.compile(r'(<!--)');
commentEnd = re.compile(r'(-->)');
keepCommentIfString='<!--@NOSTRIP';
commentStartString = '<!--';

def scanFile(env,infile, outfile):
    continuation = 0 # multiple comment lines - join lines and recheck
    lineno = 0       # line number
    incompleteLine = ""
    sfile = "" + str(infile)
    outputf = file(outfile.abspath, 'w');
    inputf = file(infile.abspath)
    while 1:
        line = inputf.readline()
        lineno = lineno + 1
    
        if not line: print ; break
        
        line = line.rstrip()
        
        #if "<!--", i.e. comment start and not  "-->", i.e. comment end save line and read next line
        if continuation > 0:
            if commentEnd.search(line) >= 0:
                continuation = 0
                line = incompleteLine + line;
                incompleteLine = ""
            else:
                incompleteLine += line;
                continue
        else:
            if (commentStart.search(line) >= 0) and not(commentEnd.search(line) >= 0):
                continuation = 1
                incompleteLine = line
                continue
        
        line_o = stripRecursive(env,line).rstrip();
        if line_o != "":
            outputf.writelines(line_o+'\n')

#strip multiple comment lines
def stripRecursive(env,line ):
    m = xmlComment.match(line)
    if m >= 0:
        comment = m.group(1)
        if re.search('<!--', comment) > 0: # careful, multiple comments
        
            # remove nested comment(s) for now
            newLine =  stripRecursive(env,m.group(1)) + m.group(m.lastindex)
            line=line.replace(line,newLine)
            return line
        else:
            if re.search(keepCommentIfString, line) > 0: # remove "comment keep string" and keep the comment
                line=line.replace(keepCommentIfString,commentStartString)
            else:
                newLine =  m.group(1) + m.group(m.lastindex)
                line=line.replace(line,newLine)
            return line
    else:
        return line



def stripXmlComments(target, source, env):
    i = 0
    
    for tfile in target:        
        scanFile(env, source[i], tfile)
        i+=1
    return 0

def stripXmlComments_emitter(target, source, env):
    output=[]
    if len(target) != 1:
        api.output.error_msg("Only one input is allowed")    
    try:
        dnodes = env.arg2nodes(target, env.fs.Dir)
    except TypeError:
        api.output.error_msg("Target `%s' is a file, but should be a directory.  Perhaps you have the arguments backwards?" % str(dir))    
    for s in source:
        path,base=os.path.split(s.path)
        output.append(env.File(base,dnodes[0]))
    
    return (output, source)

api.register.add_builder('__StripXMLComments__',SCons.Script.Builder(
        action=SCons.Script.Action(stripXmlComments),  
        emitter=stripXmlComments_emitter,
        target_factory=SCons.Node.FS.Entry
        #target_factory = SCons.Node.FS.File
        ))

    
def StripXMLComments(env,target, source, sub_dir = '.',**kw):
    if sub_dir is not '.':
        tmp_target = os.path.join(target,sub_dir)
    else:
        tmp_target = target
    
    return env.__StripXMLComments__(tmp_target,source,**kw)

def StripXMLCommentsAs(env,target,source,**kw):
    
    output = []
    for target_i,source_i in zip(target,source):
        target_path = os.path.split(str(target_i))[0]
        output += StripXMLComments(env,target_path,source_i)
    return output
        
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object  
SConsEnvironment.StripXMLComments=StripXMLComments        
SConsEnvironment.StripXMLCommentsAs=StripXMLCommentsAs