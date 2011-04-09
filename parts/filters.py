
import api
import metatag

class hasFileExtension(object):
    def __init__(self,extlist):
        self.extlist=extlist
    
    def __call__(self,node):
        for i in self.extlist:
            if fnmatch.fnmatchcase(str(node),i):
                return True
        return False
    
class HasPackageCatagory(object):
    def __init__(self, catagory):
        self.catagory=catagory
        
    def __call__(self,node):
        return metatag.MetaTagValue(node,'category','package')==self.catagory


api.register.add_global_object('hasFileExtension',hasFileExtension)   
api.register.add_global_object('HasPackageCatagory',HasPackageCatagory)   