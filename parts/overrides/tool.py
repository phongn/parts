# this override fixes some issue with tools being reloaded 
# and imporve report handling when a tools fails
import imp
import sys
import StringIO
import traceback
import SCons.Tool
from .. import api

class Parts_Tool(object):
    def __init__(self, name, toolpath=[], **kw):
        self.name = name
        self.toolpath = toolpath + SCons.Tool.DefaultToolpath
        # remember these so we can merge them into the call
        self.init_kw = kw

        module = self._tool_module()
        self.generate = module.generate
        self.exists = module.exists
        if hasattr(module, 'options'):
            self.options = module.options

    def _tool_module(self):
        # TODO: Interchange zipimport with normal initilization for better error reporting
        oldpythonpath = sys.path
        sys.path = self.toolpath + sys.path
        
        try:
            try:
                file, path, desc = imp.find_module(self.name, self.toolpath)
                full_name="{0}<{1}>".format(self.name,str(path.__hash__()))
                try:
                    return sys.modules[full_name]
                except KeyError:
                    pass
                try:
                    return imp.load_module(full_name, file, path, desc)
                finally:
                    if file:
                        file.close()
            except ImportError, e:
                ec_str=StringIO.StringIO()
                traceback.print_exc(file=ec_str)
                api.output.verbose_msg("tools","Failed to load module!")
                api.output.verbose_msg(["tools_failure","load_module"],"Stack:\n%s"%(ec_str.getvalue()))
                if str(e)!="No module named %s"%self.name:
                    raise SCons.Errors.EnvironmentError, e
                try:
                    import zipimport
                except ImportError:
                    pass
                else:
                    for aPath in self.toolpath:
                        try:
                            importer = zipimport.zipimporter(aPath)
                            return importer.load_module(self.name)
                        except ImportError, e:
                            pass
        finally:
            sys.path = oldpythonpath

        full_name = 'SCons.Tool.' + self.name
        try:
            return sys.modules[full_name]
        except KeyError:
            try:
                smpath = sys.modules['SCons.Tool'].__path__
                try:
                    file, path, desc = imp.find_module(self.name, smpath)
                    module = imp.load_module(full_name, file, path, desc)
                    setattr(SCons.Tool, self.name, module)
                    if file:
                        file.close()
                    return module
                except ImportError, e:
                    if str(e)!="No module named %s"%self.name:
                        traceback.print_exc(file=ec_str)
                        api.output.verbose_msg("tools","Failed to load module!")
                        api.output.verbose_msg(["tools_failure","load_module"],"Stack:\n%s"%(ec_str.getvalue()))
                        raise SCons.Errors.EnvironmentError, e
                    try:
                        import zipimport
                        importer = zipimport.zipimporter( sys.modules['SCons.Tool'].__path__[0] )
                        module = importer.load_module(full_name)
                        setattr(SCons.Tool, self.name, module)
                        return module
                    except ImportError, e:
                        m = "No tool named '%s': %s" % (self.name, e)
                        traceback.print_exc(file=ec_str)
                        api.output.verbose_msg("tools","Failed to load module!")
                        api.output.verbose_msg(["tools_failure","load_module"],"Stack:\n%s"%(ec_str.getvalue()))
                        raise SCons.Errors.EnvironmentError, m
            except ImportError, e:
                m = "No tool named '%s': %s" % (self.name, e)
                ec_str=StringIO.StringIO()
                traceback.print_exc(file=ec_str)
                api.output.verbose_msg("tools","Failed to load module!")
                api.output.verbose_msg(["tools_failure","load_module"],"Stack:\n%s"%(ec_str.getvalue()))
                raise SCons.Errors.EnvironmentError, m

    def __call__(self, env, *args, **kw):
        if self.init_kw is not None:
            # Merge call kws into init kws;
            # but don't bash self.init_kw.
            if kw is not None:
                call_kw = kw
                kw = self.init_kw.copy()
                kw.update(call_kw)
            else:
                kw = self.init_kw
        env.Append(TOOLS = [ self.name ])
        if hasattr(self, 'options'):
            import SCons.Variables
            if not env.has_key('options'):
                from SCons.Script import ARGUMENTS
                env['options']=SCons.Variables.Variables(args=ARGUMENTS)
            opts=env['options']

            self.options(opts)
            opts.Update(env)

        self.generate(env, *args, **kw)

    def __str__(self):
        return self.name

    def Exists(self,env, *args, **kw):
        return self.exists( env, *args, **kw)


SCons.Tool.Tool=Parts_Tool
