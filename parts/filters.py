
import common
import metatag

class hasFileExtension():
    def __init__(self,extlist):
        self.extlist=extlist
    
    def __call__(self,node):
        for i in self.extlist:
            if fnmatch.fnmatchcase(str(node),i):
                return True
        return False
    
class HasPackageCatagory():
    def __init__(self, catagory):
        self.catagory=catagory
        
    def __call__(self,node):
        return metatag.MetaTagValue(node,'category','package')==self.catagory


common.add_global_value('hasFileExtension',hasFileExtension)   
common.add_global_value('HasPackageCatagory',HasPackageCatagory)   