# this overide deals with Part providing better information for what there is a duplicated
# target/environment/builder being reproted by SCons. This allows Part to report which two
# Parts are the issues, which helps a lot when this happens across parts, as the SCons 
# message is hard to deal with by default and it does not know of "part/components"

from .. import reporter
import SCons.Builder

scons_node_errors=SCons.Builder._node_errors

def parts_node_errors(builder, env, tlist, slist):
    """SCons errors out without a lot of useful info
    This function tries to do the same tests, but report more useful stuff given that we have components
    """
    
    error=False
    warn=False
    # use basic SCons template for how it handles these error.. may append on to later
    for t in tlist:
        if t.side_effect:
            error=True
        if t.has_explicit_builder():
            if not t.env is None and not t.env is env:
                action = t.builder.action
                t_contents = action.get_contents(tlist, slist, t.env)
                contents = action.get_contents(tlist, slist, env)
                if t_contents == contents:
                    warn=True
                else:
                    error=True
            if builder.multi:
                try:
                    if t.builder != builder or t.get_executor().targets != tlist: # scons 1.x version
                        error=True
                except AttributeError:
                    if t.builder != builder or  t.get_executor().get_all_targets() != tlist:# scons 2.x version
                        error=True
            elif t.sources != slist:
                error=True
                
        if error:
            reporter.report_error('Build issue found with two different Environments\n One environment was defined in Part "%s"\n The other was defined in Part "%s"'%(t.env.get('PART_ALIAS',"<unknown>"),env.get('PART_ALIAS',"<unknown>")),show_stack=False,exit=False)
        elif warn:
            reporter.report_warning('Build issue found with two different Environments\n One environment was defined in Part "%s"\n The other was defined in Part "%s"'%(t.env.get('PART_ALIAS',"<unknown>"),env.get('PART_ALIAS',"<unknown>")),show_stack=False)

    # call the SCons code
    scons_node_errors(builder, env, tlist, slist)
    
SCons.Builder._node_errors=parts_node_errors
