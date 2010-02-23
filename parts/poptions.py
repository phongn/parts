
import common
import color
import reporter
import logger
import load_module
import platform_info

import SCons.Script    

import sys
from optparse import OptionValueError


# used to help scripts set defaults when there is no config script
def SetOptionDefault(key,value):

    def_env=SCons.Script.DefaultEnvironment()
    
    args = sys.argv[1:]
    if common.g_part_mode=='help':
        return
    global def_args
    #special logger logic
    if key=='LOGGER':
        ### clean up
        directory=def_env.Dir(def_env['LOG_ROOT_DIR'])
        tmp=def_env.subst(value)
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
        if type(reporter.g_rpter.logger) is logger.QueueLogger:
            log_obj=log_obj(directory.abspath,def_env['LOG_FILE_NAME'])
            reporter.g_rpter.reset_logger(log_obj)
        elif type(reporter.g_rpter.logger) is not logger.nil_logger:
            reporter.print_msg('Logger already set -- ignoring')
            
    reporter.print_msg('Setting default value of',key,'to',value)
    common.g_defaultoverides[key]=value
    #reset cache 
    #common.g_env_cache={}


def opt_target(option, opt, value, parser):
    lst=value.split('-')
    if len(lst) > 2:
        raise OptionValueError("Error:  %s is not a valid --target_platform value\nValue must be in form of <Plaform>-<Architecture>" % o)
    if len(lst) == 1:
        # nice to a have short cut
        tmp=platform_info.MapArchitecture(lst[0])
        if tmp == '':
            #assume this was a platform
            parser.values.target_platform=platform_info.SystemPlatform(
                lst[0],platform_info._host_sys.ARCH
                )
        else:
            #assume this is a architure
            parser.values.target_platform=platform_info.SystemPlatform(
                    platform_info._host_sys.OS,lst[0]
                    )
    else:
        p=lst[0]
        a=lst[1]
        if p == '':
            p=platform_info._host_sys.OS
        if a == '':
            a=platform_info._host_sys.Architecture
        parser.values.target_platform=platform_info.SystemPlatform(p,a)

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

def opt_bool(option, opt, value, parser,var):
    tmp=value.lower()
    if tmp in opt_true_values:
        parser.values.__dict__[var]=True
    elif tmp in opt_false_values:
        parser.values.__dict__[var]=False
    else:
        raise OptionValueError("Error: Invalid value for boolean option: %s" % value)

def opt_color(option, opt, value, parser):
    tmp=value.lower()
    colors=False
    if tmp in opt_false_values:
        colors=None
    elif os.isatty(sys.stdout.fileno()) or os.isatty(sys.stderr.fileno()):
        # if the text is being redirected
        colors=None
    elif tmp in set(['full','default','darkbg','y', 'yes', 'true', 't', '1', 'on' ]):
        colors={
            'stdout':color.ConsoleColor(color.Dim),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(color.Bright),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            }
    elif tmp in ['simple']:
        colors={
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
            'stdout':color.ConsoleColor(color.Dim),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(color.Bright),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            }
        for t in tmp:
            # stuff like "o=blue,e=green"
            k,v=t.split('=')
            k=k.lower()
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
        raise OptionValueError("Error: Invalid value for setting color: %s" % value)
    
    parser.values.use_color=colors
    
def opt_ccopy(option, opt, value, parser):
    tmp=value.lower()
    if tmp in ['hard-soft-copy','soft-hard-copy','soft-copy','hard-copy','copy']:
        parser.values.ccopy_logic=tmp
        return
    raise OptionValueError("Error: Invalid value for ccopy-logic: %s, value must be one of %s" % (value,['hard-soft-copy','soft-hard-copy','soft-copy','hard-copy','copy']))
    
def opt_logging(option, opt, value, parser):
    tmp=value.lower()
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


SCons.Script.AddOption("--cfg-file",
            dest='cfg_file',
            default='parts.cfg',
            nargs=1, type='string',
            action='store',
            help='Configuration file used to store common settings')

SCons.Script.AddOption("--verbose",
            dest='verbose',
            default=[],
            callback=lambda option, opt, value, parser:opt_list(option, opt, value, parser,'verbose'),
            nargs=1, type='string',
            action='callback',
            help='Control the level of detail information printed')
            
SCons.Script.AddOption("--log",
            dest='logger',
            default=logger.QueueLogger,
            nargs=1,
            callback=opt_logging,
            type='string',
            action='callback',
            help='True to use default logger, else name of logger to use')

SCons.Script.AddOption("--build-config","--buildconfig","--cfg",
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
            default=True,
            nargs=1,
            callback=lambda option, opt, value, parser:opt_bool(option, opt, value, parser,'show_progress'),
            type='string',
            action='callback',
            help='Controls if progress state is shown')  

SCons.Script.AddOption("--use-color","--color",
            dest='use_color',
            default={
            'stdout':color.ConsoleColor(color.Dim),
            'stderr':color.ConsoleColor(color.BrightRed),
            'stdwrn':color.ConsoleColor(color.BrightYellow),
            'stdmsg':color.ConsoleColor(color.Bright),
            'stdverbose':color.ConsoleColor(color.BrightAqua),
            'stdtrace':color.ConsoleColor(color.BrightBlue),
            },
            nargs=1,
            callback=opt_color,
            type='string',
            action='callback',
            help='Controls if console color support is used')

SCons.Script.AddOption("--ccopy",'--copy-logic',
            dest='ccopy_logic',
            default=None,
            nargs=1,
            callback=opt_ccopy,
            type='string',
            action='callback',
            help='Values used to control different build mode for a given part') 

common.add_global_value('SetOptionDefault',SetOptionDefault)