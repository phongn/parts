
class toolvar(str):
    def __new__(self, command,type_list=[]):
        return str.__new__(self, command)
    
    def __init__(self,command,type_list=[]):
        self.__tlist=type_list

    def __eq__(self,val):
        return super(toolvar, self).__eq__(val) or val in self.__tlist

    def __ne__(self,val):
        return not self.__eq__(val)

