
import os.path
import string
import sys

from ListVariable import ListVariable2

import SCons.Environment,SCons.Util

''' 
this will be a modified version of the Variable object used by SCons
Since i can't overide it in a nice way, I will may my own compatible type
From the Environment point of view
'''

class Variables:

    """
    Holds all the options, updates the environment with the variables,
    and renders the help text.
    """
    def __init__(self, files=[], args={}, user_defaults={}):
        """
        files - List of option configuration files to load
        args - the ARGUMENTS
        user_defaults - value to overide the defined varaible defaults with
        """
        self.options = {}
        if args is None:
            args={}
        self.args = args
        if not SCons.Util.is_List(files):
            if files != None:
                files = [ files ]
            else:
                files = []
        self.files = files
        self.user_defaults=user_defaults
        self.unknown = {}


    def _do_add(self, key, help="", default=None, validator=None, converter=None):
        #scons defined this as holder object.. keep same value to be safe
        class Variable:
            pass

        option = Variable()

        # if we get a list or a tuple, we take the first element as the
        # option key and store the remaining in aliases.
        # note in orignal SCons case this is stored as a list not in a dict
        # need make sure alias search is still fast
        if SCons.Util.is_List(key) or SCons.Util.is_Tuple(key):
            option.key     = key[0]
            option.aliases = key[1:]
        else:
            option.key     = key
            option.aliases = []
        option.help = help
        option.default = default
        option.validator = validator
        option.converter = converter
        
        if self.options.has_key(option.key):
            print "Varible option [",option.key,"] is was already defined"
        self.options[option.key]=option

    def keys(self):
        """
        Returns the keywords for the options
        """
        return self.options.keys()

    def Add(self, key, help="", default=None, validator=None, converter=None, **kw):
        """
        Add an option.

        key - the name of the variable, or a list or tuple of arguments
        help - optional help text for the options
        default - optional default value
        validator - optional function that is called to validate the option's value
                    Called with (key, value, environment)
        converter - optional function that is called to convert the option's value before
                    putting it in the environment. called with a 
        **kw -- ignored.. for ability to support changes in the future, and allows apply to work 
        """

        if SCons.Util.is_List(key) or type(key) == type(()):
            #   This does a simple validation check for token based text allowed as varibles
            for k in key:
                if not SCons.Util.is_String(k) or \
                not SCons.Environment.is_valid_construction_var(k):
                    raise SCons.Errors.UserError, "Illegal Variables.Add() key `%s'" % str(k)
        else:
            # This does a simple validation check for token based text allowed as varibles
            if not SCons.Util.is_String(key) or \
               not SCons.Environment.is_valid_construction_var(key):
                raise SCons.Errors.UserError, "Illegal Variables.Add() key `%s'" % str(key)

        self._do_add(key, help, default, validator, converter)

    def AddVariables(self, *optlist):
        """
        Add a list of options.

        Each list element is a tuple/list of arguments to be passed on
        to the underlying method for adding options.

        Example:
          opt.AddVariables(
            ('debug', '', 0),
            ('CC', 'The C compiler'),
            ('VALIDATE', 'An option for testing validation', 'notset',
             validator, None),
            )
        """
        for o in optlist:
            self.Add(*o)


    def Update(self, env, args=None):
        """
        Update an environment with the option variables.

        env - the environment to update.
        """

        # this is the dict with the final values
        values = {}

        # first fill in all options value with default values
        for k,option in self.options.iteritems():
            #if not option.default is None:
            values[k] = option.default
            #add any default overides
            if self.user_defaults.has_key(k):
                values[k] = self.user_defaults[k]

        # next set the value specified in the options file
        # keep as SCons has it orginally
        for filename in self.files:
            if os.path.exists(filename):
                dir = os.path.split(os.path.abspath(filename))[0]
                if dir:
                    sys.path.insert(0, dir)
                try:
                    values['__name__'] = filename
                    exec string.replace(open(filename).read(), '\r', '\n') in {}, values
                finally:
                    if dir:
                        del sys.path[0]
                    del values['__name__']

        # set the values specified on the command line
        # if None, SCons is not passing any to us 
        if args is None:
            #use the user supplied arguments, if this is the case
            args = self.args
        
        #Override any value we have with Arguments provided
        for arg, value in args.iteritems():
            # we need to see if there is a alias for this
            # for each option we need to test if this is an alias+key that
            # is a match for the arg
            for k,option in self.options.iteritems():
                if arg in option.aliases + [ k ]:
                    # we have a match, so store and break for this argument
                    values[k] = value
                    break
            else:
                # no match was found so we store this in unknowns
                self.unknown[arg] = value
                print "^^^^",arg,value

        # at this point the values should up to date
        # we need to apply any convertion and validate the value after addition
        # orginal form in SCon does this in three loops, I do it in two
        
        # put the variables in the environment:
        # seem odd at first but allows the string version of the value to be 
        # subst()ed correctly for converion call
        for k,v in values.iteritems():
            env[k] = v
        
        for k,v in values.iteritems():
            # There is a possiblility that unkown values have been read by the cfg file
            # This code will rtry to get the option and if that fails adds it to the unknowns
            tmp=self.options.get(k,None)
            if tmp is None:
                # This value was read in from a file most likely
                print "****",k,v
                self.unknown[k] = v
                continue
            tmp=tmp.converter
            
            if self.options[k].converter is not None:
                # call converter
                value = env.subst('${%s}'%k)
                try:
                    try:
                        env[k] = tmp(str_val=value, raw_val=v)
                    except TypeError:
                        try:
                            env[k] = tmp(value)
                        except TypeError:
                            env[k] = tmp(value,env)
                except ValueError, x:
                    raise SCons.Errors.UserError, 'Error converting option: %s\n%s'%(k, x)
            tmp=self.options[k].validator
            
            if tmp is not None:
                tmp(k, env.subst('${%s}'%k), env)
        
    def UnknownVariables(self):
        """
        Returns any options in the specified arguments lists that
        were not known, declared options in this object.
        """
        return self.unknown

    def Save(self, filename, env):
        """
        Saves all the options in the given file.  This file can
        then be used to load the options next run.  This can be used
        to create an option cache file.

        filename - Name of the file to save into
        env - the environment get the option values from
        """

        # Create the file and write out the header
        try:
            fh = open(filename, 'w')

            try:
                # Make an assignment in the file for each option
                # within the environment that was assigned a value
                # other than the default.
                for k,option in self.options.iteritems():
                    try:
                        value = env[k]
                        try:
                            # if this is an object this call allow a way to 
                            # for a string to store it
                            prepare = value.prepare_to_store()
                        except AttributeError:
                            # if that is not provided try to 
                            # use the python way to show the object
                            try:
                                eval(repr(value))
                            except KeyboardInterrupt:
                                raise
                            except:
                                # Convert stuff that has a repr() that
                                # cannot be evaluated into a string
                                value = SCons.Util.to_String(value)
                        
                        ## skipping logic for not writting value if equal to default for now
                        # get default to see if we should store this
                        #defaultVal = env.subst(SCons.Util.to_String(option.default))
                        #if option.converter:
                        #    defaultVal = option.converter(defaultVal)
                        #if str(env.subst('${%s}' % option.key)) != str(defaultVal):
                        
                        fh.write('%s = %s\n' % (option.key, repr(value)))
                    except KeyError:
                        pass
            finally:
                fh.close()

        except IOError, x:
            raise SCons.Errors.UserError, 'Error writing options to file: %s\n%s' % (filename, x)

    # so what is messed up is that thsi expects that all values are string like
    # this is not the case as we have objects and lists, however objects
    # can't be stated in anyform on the command line, only cfg files
    def GenerateHelpText(self, env, sort=None):
        """
        Generate the help text for the options.

        env - an environment that is used to get the current values
              of the options.
        """

        if sort:
            options = self.options.values()
            options.sort(cmp=lambda x,y: cmp(x.key, y.key))
        else:
            options = self.options.values()

        def format(opt, self=self, env=env):
            if env.has_key(opt.key):
                actual = env.subst('${%s}' % opt.key)
            else:
                actual = None
            return self.FormatVariableHelpText(env, opt.key, opt.help, opt.default, actual, opt.aliases)
        
        lines = filter(None, map(format, options))

        return string.join(lines, '')

    format  = '\n%s: %s\n    default: %s\n    actual: %s\n'
    format_ = '\n%s: %s\n    default: %s\n    actual: %s\n    aliases: %s\n'

    def FormatVariableHelpText(self, env, key, help, default, actual, aliases=[]):
        # Don't display the key name itself as an alias.
        aliases = filter(lambda a, k=key: a != k, aliases)
        if len(aliases)==0:
            return self.format % (key, help, default, actual)
        else:
            return self.format_ % (key, help, default, actual, aliases)

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
