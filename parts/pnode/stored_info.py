

class stored_info(object):
    """description of class"""
    __slots__=[]
    def post_load_convet(self):
        '''
        This function is called to convert any data into strong types.
        Certain object just work better if we store them as strings, or something else
        and reconvert them after loading.
        '''
        pass
        
