import stored_info
from .. import platform_info
class part_info(stored_info.stored_info):
    """description of class"""
    def __init__(self):
        
        self.name=''
        self.short_name=''
        self.alias=''
        self.short_alias=''
        self.version=None
        self.root=None
        self.target_platform=''
        self.config=''
        self.platform_match=''
        self.package_group='' 
        self.mode=[]
        self.subparts=set()
        self.parents=[]
        self.parent=None
        self.sections={}
        self.file={} # file.ninfo plus name
        self.src_path=None # Node
        self.sdk_file={} #???
        self.build_context=[]
        self.config_context=[]
        self.force_load=False
        self.kw={}
        
    
    def post_load_convet(self):
        self.target_platform=platform_info.SystemPlatform(self.target_platform)
        self.platform_match=platform_info.SystemPlatform(self.platform_match)
        
