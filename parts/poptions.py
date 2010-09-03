
import common
import color
import reporter
import logger
import load_module
import platform_info

import SCons.Script    
import os
import sys
from optparse import OptionValueError


# used to help scripts set defaults when there is no config script
def SetOptionDefault(key,value):

    args = sys.argv[1:]
    if common.g_engine._build_mode=='help':
        return
    global def_args
    #special logger logic
    if key=='LOGGER':
        if type(reporter.g_rpter.logger) is not logger.QueueLogger:
            #reporter.print_msg('Logger already set -- ignoring')
            pass
        else:
            ### clean up
            def_env=SCons.Script.DefaultEnvironment()
            directory=def_env.Dir(def_env['LOG_ROOT_DIR'])
            tmp=def_env.subst(value)
            if tmp=='TEXT_LOGGER':
                tmp=def_env.subst('$'+value)

            if tmp in opt_true_values :
                mod=load_module.load_module(
                    load_module.get_site_directories('loggers'),
                    'text',
                    'logger')  
                log_obj=mod.__dict__.get(value,logger.nil_logger)
            elif tmp in opt_false_values:
                log_obj=logger.nil_logger
            else:
                mod=load_module.load_module(
                    load_module.get_site_directories('loggers'),
                    tmp,
                    'logger')  
                log_obj=mod.__dict__.get(tmp,logger.nil_logger)
            #####
            log_obj=log_obj(directory.abspath,def_env['LOG_FILE_NAME'])
            reporter.g_rpter.reset_logger(log_obj)
            
    reporter.print_msg('Setting default value of',key,'to',value)
    common.g_defaultoverides[key]=value
    SetOptionDefault._modified=True


def opt_target(option, opt, value, parser):
    
    tmp=platform_info.target_convert(value,error=False)
    if tmp is None:
        raise OptionValueError("Error:  %s is not a valid --target_platform value\nValue must be in form of <Plaform>-<Architecture>" % value)
    
    parser.values.target_platform=tmp

def opt_chain(option, opt, value, parser):
    tmp=value.split(',')
    lst=[]
    for i in tmp:
        lst.append(i.split('_'))
    parser.values.tool_chain=lst
    
def opt_list(option, opt, value, parser,var): 
    parser.values.__dict__[var]=value.split(',')
    
opt_true_values  = set(['y', 'yes', 'true', 't', '1', 'on' , 'all' ])
opt_false_values = set(['n', 'no', 'false', 'f', '0', 'off', 'none'])

def opt_bool(option, opt, value, parser,var,negate=False):
    if negate: 
        TrueValue=False
    else:
        TrueValue=True
    if value is None:
        print 1,TrueValue,option
        parser.values.__dict__[var]=TrueValue
        return
    tmp=value.lower()
    if tmp in opt_true_values:
        print 2
        parser.values.__dict__[var]= TrueValue
    elif tmp in opt_false_values:
        print 3
        parser.values.__dict__[var]= not TrueValue
    else:
        raise OptionValueError('Invalid value for boolean option "%s" value "%s"\n Valid options are %s' % 
                (var.replace('-','_'),value,opt_true_values|opt_false_values))

def opt_bool_enum(option, opt, value, parser,var,enum,negate=False):
    if value is None:
        parser.values.__dict__[var]=True
        return
    tmp=value.lower()
    if tmp in opt_true_values:
        parser.values.__dict__[var]=True
    elif tmp in opt_false_values:
        parser.values.__dict__[var]=False
    elif tmp in enum:
        parser.values.__dict__[var]=tmp
    else:
        raise OptionValueError('Invalid value for option "%s" value "%s"\n Valid options are %s' % 
                (var.replace('-','_'),value,set(enum)|opt_true_values|opt_false_values))


def opt_color(option, opt, value, parser):
    if value is None:
        value='true'
    tmp=value.lower()
    colors=False
    if tmp in opt_false_values:
        colors=None
    elif tmp in set(['full','default','darkbg','y', 'yes', 'true', 't', '1', 'on' ]):
        colors={
            'console': color.ConsoleColor(color.BrightMagenta),
            'stdout':color.ConsoleColor(color.Dim),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(color.Bright),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            }
    elif tmp in ['simple']:
        colors={
            'console':color.ConsoleColor(color.Bright),
            'stdout':color.ConsoleColor(),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            }

    else:
        tmp=value.split(',')
        colors={
            'console':color.ConsoleColor(color.BrightMagenta),
            'stdout':color.ConsoleColor(color.Dim),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(color.Bright),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            }
        for t in tmp:
            # stuff like "o=blue,e=green"
            try:
                # need better lgic to validate arguments.. but this will do for now
                k,v=t.split('=')
            except:
                raise OptionValueError("Error: Invalid value for setting color: %s" % value)
            k=k.lower()
            if k in ['con','tty','console']:
                colors['console']=color.parse_color(v)
            if k in ['o','out','stdout']:
                colors['stdout']=color.parse_color(v)
            if k in ['e','err','error','stderr']:
                colors['stderr']=color.parse_color(v)
            if k in ['w','wrn','warning','stdwrn']:
                colors['stdwrn']=color.parse_color(v)
            if k in ['m','msg','message','stdmsg']:
                colors['stdmsg']=color.parse_color(v)
            if k in ['v','ver','verbose','stdverbose']:
                colors['stdverbose']=color.parse_color(v)
            if k in ['t','trace','stdtrace']:
                colors['stdtrace']=color.parse_color(v)
    if colors==False:
        raise OptionValueError("Invalid value for setting color: %s" % value)
    
    parser.values.use_color=colors
    
    
def opt_logging(option, opt, value, parser):
    if value is None:
        value ='text'
    tmp=value.lower()
    try:
        if tmp in opt_true_values:
            def_logger='text'
            mod=load_module.load_module(
                load_module.get_site_directories('loggers'),
                def_logger,
                'logger')
            parser.values.logger=mod.__dict__.get(def_logger,logger.nil_logger)
        elif tmp in opt_false_values:
            parser.values.logger=logger.nil_logger
        else:
            mod=load_module.load_module(
                load_module.get_site_directories('loggers'),
                value,
                'logger')
            parser.values.logger=mod.__dict__.get(value,logger.nil_logger)
    except ImportError:
        raise OptionValueError('No logger called "%s" was found' % value)


SCons.Script.AddOption("--verbose",
            dest='verbose',
            default=[],
            callback=lambda option, opt, value, parser:opt_list(option, opt, value, parser,'verbose'),
            nargs=1, type='string',
            action='callback',
            help='Control the level of detailed verbose information printed')
            
SCons.Script.AddOption("--trace",
            dest='trace',
            default=[],
            callback=lambda option, opt, value, parser:opt_list(option, opt, value, parser,'trace'),
            nargs=1, type='string',
            action='callback',
            help='Control the level of trace information printed')
            
SCons.Script.AddOption("--log",
            dest='logger',
            default=logger.QueueLogger,
            nargs='?',
            callback=opt_logging,
            type='string',
            action='callback',
            help='True to use default logger, else name of logger to use')

SCons.Script.AddOption("--build-config","--buildconfig","--bldcfg","--bcfg","--cfg",
            dest='build_config',
            default=None,
            nargs=1, type='string',
            action='store',
            help='The configuration to use')
                 
SCons.Script.AddOption("--tool-chain","--toolchain","--tc",
            dest='tool_chain',
            default=None,
            nargs=1,
            callback=opt_chain,
            type='string',
            action='callback',
            help='Tool chains to use for build')
            
SCons.Script.AddOption("--target","--target-platform",
            dest='target_platform',
            default=None,
            nargs=1,
            callback=opt_target,
            type='string',
            action='callback',
            help='Sets the default TARGET_PLATFORM use for cross builds')

SCons.Script.AddOption("--mode",
            dest='mode',
            default=None,
            nargs=1,
            callback=lambda option, opt, value, parser:opt_list(option, opt, value, parser,'mode'),
            type='string',
            action='callback',
            help='Values used to control different build mode for a given part')  
        
SCons.Script.AddOption("--show-progress",
            dest='show_progress',
            nargs='?',
            callback=lambda option, opt, value, parser:opt_bool(option, opt, value, parser,'show_progress'),
            type='string',
            action='callback',
            help='Controls if progress state is shown')
            
SCons.Script.AddOption("--hide-progress",
            dest='show_progress',
            default=True,
            action="store_false",
            help='Controls if progress state is shown')

SCons.Script.AddOption("--enable-parts-cache",
            dest="parts_cache",
            default=True,
            action="store_true",
            help='Enable Parts data to be used cache')
            
SCons.Script.AddOption("--disable-parts-cache",
            dest="parts_cache",
            default=True,
            action="store_false",
            help='Disable Parts data cache from being used')
                        
SCons.Script.AddOption("--disable-incremental-cache","--disable-inc-cache", 
            dest="incremental_cache",
            default=True,
            action="store_false",
            help='Disable Parts fast incremental logic')

SCons.Script.AddOption("--disable-incremental-dependent-checks",
            dest="incremental_dependent_checks",
            default=True,
            action="store_false",
            help='Assume the dependents are up-to-date. Skipping update checks on dependents. May result in corrupt build!!!')
            
SCons.Script.AddOption("--disable-update-check-exit",
            dest="update_check_exit",
            default=True,
            action="store_false",
            help='Enable Parts to exit early if the update checks return True, forcing SCons longer (but possibily more correct) checks to happen')            


##SCons.Script.AddOption("--use-sdk",
##            dest='use_sdk',
##            default=False,
##            nargs='?',
##            callback=lambda option, opt, value, parser:opt_bool_enum(option, opt, value, parser,'show_progress',['force','auto']),
##            type='string',
##            action='callback',
##            help='Controls if progress state is shown')  

SCons.Script.AddOption("--enable-color","--use-color","--color",
            dest='use_color',            
            nargs='?',
            callback=opt_color,
            type='string',
            action='callback',
            help='Controls if console color support is used')
            
SCons.Script.AddOption("--disable-color",
            dest='use_color',
            default={
            'console':color.ConsoleColor(color.BrightMagenta),
            'stdout':color.ConsoleColor(color.Dim),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(color.Bright),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            'defaults':True
            },
            callback=lambda option, opt, value, parser:opt_color(option,opt,False,parser),
            type='string',
            action='callback',
            help='Controls if console color support is used')

SCons.Script.AddOption("--ccopy",'--ccopy-logic','--copy-logic',
            dest='ccopy_logic',
            default=None,
            nargs=1,
            #callback=opt_ccopy,
            type='choice',
            choices=['hard-soft-copy','soft-hard-copy','soft-copy','hard-copy','copy'],
            action='store',
            help='Control how Parts copy logic will work must be hard-soft-copy,soft-hard-copy, soft-copy, hard-copy, copy') 

SCons.Script.AddOption("--vcs-job",'--vcsj','--vj',
            dest='vcs_jobs',
            default=0,
            nargs=1,
            type='int',
            action='store',
            help='Level of concurrent VCS checkouts/updates that can happen at once. Defaults to -j value if not set') 

# move to end as work around to a bug in SCons            
SCons.Script.AddOption("--cfg-file","--config-file",
            dest='cfg_file',
            default='parts.cfg',
            nargs=1, type='string',
            action='store',
            help='Configuration file used to store common settings')


common.add_global_value('SetOptionDefault',SetOptionDefault)