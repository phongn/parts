
import subprocess
import os
import copy
import re

def normalize_env(shellenv, keys):
    """Given a dictionary representing a shell environment, add the variables
    from os.environ needed for the processing of .bat files; the keys are
    controlled by the keys argument.

    It also makes sure the environment values are correctly encoded.

    Note: the environment is copied"""
    normenv = {}
    if shellenv:
        for k in shellenv.keys():
            normenv[k] = copy.deepcopy(shellenv[k]).encode('mbcs')

        for k in keys:
            if os.environ.has_key(k):
                normenv[k] = os.environ[k]

    return normenv


def get_output(script, args = None, shellenv = None):
    """Parse the output of given bat file, with given args."""
    if args:
        #print("Calling '%s %s'" % (script, args))
        popen = subprocess.Popen('"%s" %s & set' % (script, args),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=shellenv)
    else:
        #print("Calling '%s'" % script)
        popen = subprocess.Popen('"%s" & set' % script,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=shellenv)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    stdout = popen.stdout.read()
    if popen.wait() != 0:
        raise IOError(popen.stderr.read())

    output = stdout
    return output



def parse_output(output, keep = None):

    ret={} #this is the data we will return
    
    ## parse everything
    reg=re.compile('(\\w*)=(.*)', re.I)
    for line in output.splitlines():
        m=reg.match(line)
        if m:
            if keep is not None:
                #see if we need to filter out data
                k=m.group(1)
                if k in keep:
                    ret[k]=m.group(2)#.split(os.pathsep)
            else:
                # take everything
                ret[m.group(1)]=m.group(2)#.split(os.pathsep)

    #see if we need to filter out data
    if keep is not None:
        pass

    return ret


def get_script_env(env,script,args=None,vars=None):
    ''' 
    this function returns a dictionary of all the data we want to merge
    or process in some other way.
    '''
    if env['PLATFORM']=='win32':
        nenv = normalize_env(env['ENV'], ['COMSPEC'])
    else:
        nenv = normalize_env(env['ENV'], [])
    output = get_output(script,args,nenv)
    vars = parse_output(output, vars)
    
    return vars



def merge_script_vars(env,script,args=None,vars=None):
    '''
    This merges the data retieved from the script in to the Enviroment
    by prepending it.
    script is the name of the script, args is optional arguments to pass
    vars are var we want to retrieve, if None it will retieve everything found
    '''
    shell_env=get_script_env(env,script,args,vars)
    for k, v in shell_env.items():
        env.PrependENVPath(k, v, delete_existing=1)

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object  
SConsEnvironment.MergeScriptVaribles=merge_script_vars
SConsEnvironment.GetScriptVarible=get_script_env
