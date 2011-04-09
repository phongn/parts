import SCons.Script

from .. import glb
from .. import common

# no need to redirect data.. assume it is correct.
def error_msg(*lst,**kw):
    glb.engine.HadError=True
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    glb.rpter.part_error(msg,kw.get('stackframe',None),kw.get('show_stack',True),kw.get('exit',True))

def warning_msg(*lst,**kw):
    msg=map(str,lst)
    msg=kw.get('sep',' ').join(msg)+kw.get('end','\n')
    glb.rpter.part_warning(msg,kw.get('print_once',False),kw.get('stackframe',None),kw.get('show_stack',True))
    
def print_msg(*lst,**kw):
    msg=map(str,lst)
    glb.rpter.part_message(kw.get('sep',' ').join(msg)+kw.get('end','\n'),kw.get('show_prefix',True))

def _verbose_msg(catagory,*lst,**kw):
    catagory=common.make_list(catagory)
    catagory.append('all')
    if glb.rpter.isSetup==False:
        glb.rpter.verbose=SCons.Script.GetOption('verbose')
    if glb.rpter.verbose is None: glb.rpter.verbose=[]
    glb.rpter.verbose_msg(catagory,[kw.get('sep',' ')]+list(lst)+[kw.get('end','\n')])

verbose_msg=_verbose_msg
        
def _trace_msg(catagory,*lst,**kw):
    catagory=common.make_list(catagory)
    if glb.rpter.isSetup==False:
        glb.rpter.trace=SCons.Script.GetOption('trace')
    if not glb.rpter.trace: glb.rpter.trace=[]
    glb.rpter.trace_msg(catagory,[kw.get('sep',' ')]+list(lst)+[kw.get('end','\n')])

trace_msg=_trace_msg

def policy_msg(policy,catagory,*lst,**kw):
    from  .. import policy as Policy
    if policy == Policy.ReportingPolicy.ignore:
        return
    elif policy == Policy.ReportingPolicy.message:
        print_msg(*lst,**kw)
    elif policy == Policy.ReportingPolicy.verbose:
        verbose_msg(catagory,*lst,**kw)
    elif policy == Policy.ReportingPolicy.warning:
        warning_msg(*lst,**kw)
    elif policy == Policy.ReportingPolicy.error:
        error_msg(*lst,**kw)


def console_msg(*lst,**kw):
    msg=map(str,lst)
    glb.rpter.stdconsole(kw.get('sep',' ').join(msg)+kw.get('end','\r'))