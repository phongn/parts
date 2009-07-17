
import string
import SCons.Util


def _converter(str_val, raw_val, allowedElems=[], mapdict={}):
    """
    """

    # make the list
    if SCons.Util.is_List(raw_val):
        val = raw_val
    else:
        val = filter(None, str_val.split(','))
    
    # map values
    val = map(lambda v, m=mapdict: m.get(v, v), val)
    
    # test for allowed value is allowed values has a value
    if allowedElems != []:
        # validate if we have bad elements
        notAllowed = filter(lambda v, aE=allowedElems: not v in aE, val)
        if notAllowed:
            raise ValueError("Invalid value(s) for option: %s" %
                        string.join(notAllowed, ','))
                        
    # see if we have duplicate elements
    notAllowed = filter(lambda v,lst=val: lst.count(v)>1, val)
    if notAllowed:
        raise ValueError("Value(s) are entered more then once for option: %s" %
                    string.join(make_unique(notAllowed), ','))
                    
    return val


def ListVariable2(key, help, default=[], names=[], map={}):
    """
    """
    names_str = 'allowed names: %s' % string.join(names, ' ')
    #if SCons.Util.is_List(default):
    #    default = string.join(default, ',')
    help = string.join(
        (help, '(comma-separated list of names)', names_str),
        '\n    ')
    return (key, help, default,
            None, #_validator,
            lambda str_val, raw_val, elems=names, m=map: _converter(str_val, raw_val, elems, m))


# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
