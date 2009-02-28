
import copy
import os
import subprocess
import re

import SCons.Util


logfile = os.environ.get('SCONS_MSCOMMON_DEBUG')
if logfile:
    try:
        import logging
    except ImportError:
        debug = lambda x: open(logfile, 'a').write(x + '\n')
    else:
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
        debug = logging.debug
else:
    debug = lambda x: None

# this is basic cache of known data
FOUND_VC={
'x86':{},
'x86_64':{},
'ia64':{}
}
SupportedVCList=[]


def program_files_dir():
    # we need the 32-bit key as all VS version are 32-bit for the forseeable future
    key='Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir'
    if is_win64():
        key='Software\\Microsoft\\Windows\\CurrentVersion\\ProgramFilesDir (x86)'
    return read_reg(key)

def is_win64():
    """Return true if running on windows 64-bits OS."""
    # Unfortunately, python does not provide any way to tell if the OS itself
    # is 32-bit or 64-bit. What is worse is that 32-bit vs 64-bit python effects
    # the value Python might return. This tell us nothing of the current system
    # The test below returns
    value = "Software\Wow6432Node"
    yo=None
    try:
        yo = SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)
    except:
        pass
    if yo is None:
        return False
    else:
        return True

def _subst_(value,pmap):

    # make an Env with no tools ( would like better way to do subst.. not sure how)
    # steve, I don't have a better way to do this with the current subst that i know of
    env=SCons.Script.Environment(tools=[],**pmap) 
    #print  env.subst(value[0])
    return env.subst(value)

def read_reg(value):
    return SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, value)[0]

# Functions for fetching environment variable settings from batch files.

def normalize_env(env, keys):
    """Given a dictionary representing a shell environment, add the variables
    from os.environ needed for the processing of .bat files; the keys are
    controlled by the keys argument.

    It also makes sure the environment values are correctly encoded.

    Note: the environment is copied"""
    normenv = {}
    if env:
        for k in env.keys():
            normenv[k] = copy.deepcopy(env[k]).encode('mbcs')

        for k in keys:
            if os.environ.has_key(k):
                normenv[k] = os.environ[k].encode('mbcs')

    return normenv

def get_output(vcbat, args = None, env = None):
    """Parse the output of given bat file, with given args."""
    if args:
        debug("Calling '%s %s'" % (vcbat, args))
        popen = subprocess.Popen('"%s" %s & set' % (vcbat, args),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)
    else:
        debug("Calling '%s'" % vcbat)
        popen = subprocess.Popen('"%s" & set' % vcbat,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    stdout = popen.stdout.read()
    if popen.wait() != 0:
        raise IOError(popen.stderr.read().decode("mbcs"))

    output = stdout.decode("mbcs")
    return output

def parse_output(output, keep = ("INCLUDE", "LIB", "LIBPATH", "PATH")):
    # dkeep is a dict associating key: path_list, where key is one item from
    # keep, and pat_list the associated list of paths

    # TODO(1.5):  replace with the following list comprehension:
    #dkeep = dict([(i, []) for i in keep])
    dkeep = dict(map(lambda i: (i, []), keep))

    # rdk will  keep the regex to match the .bat file output line starts
    rdk = {}
    for i in keep:
        rdk[i] = re.compile('%s=(.*)' % i, re.I)

    def add_env(rmatch, key):
        plist = rmatch.group(1).split(os.pathsep)
        for p in plist:
            # Do not add empty paths (when a var ends with ;)
            if p:
                p = p.encode('mbcs')
                # XXX: For some reason, VC98 .bat file adds "" around the PATH
                # values, and it screws up the environment later, so we strip
                # it. 
                p = p.strip('"')
                dkeep[key].append(p)

    for line in output.splitlines():
        for k,v in rdk.items():
            m = v.match(line)
            if m:
                add_env(m, k)

    return dkeep

def script_env(env,batfilename):

    vars = ('LIB', 'LIBPATH', 'PATH', 'INCLUDE')

    nenv = common.normalize_env(env['ENV'], ['COMSPEC'])
    output = common.get_output(batfilename, env=nenv)
    vars = common.parse_output(output, vars)
    
    return vars

# TODO(sgk): unused
def output_to_dict(output):
    """Given an output string, parse it to find env variables.

    Return a dict where keys are variables names, and values their content"""
    envlinem = re.compile(r'^([a-zA-z0-9]+)=([\S\s]*)$')
    parsedenv = {}
    for line in output.splitlines():
        m = envlinem.match(line)
        if m:
            parsedenv[m.group(1)] = m.group(2)
    return parsedenv

# TODO(sgk): unused
def get_new(l1, l2):
    """Given two list l1 and l2, return the items in l2 which are not in l1.
    Order is maintained."""

    # We don't try to be smart: lists are small, and this is not the bottleneck
    # is any case
    new = []
    for i in l2:
        if i not in l1:
            new.append(i)

    return new
