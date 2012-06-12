

class stored_info(object):
    """description of class"""

    def post_load_convet(self):
        '''
        This function is called to convert any data into strong types.
        Certain object just work better if we store them as strings, or something else
        and reconvert them after loading.
        '''
        pass
        
    #def __getstate__(self):
    #    print "called base"
    #    tmp={}
    #    for k,v in self.__dict__.iteritems():
    #        if k.startswith('__') == False:
    #            tmp[k]=v
    #    print tmp
    #    return tmp
    #