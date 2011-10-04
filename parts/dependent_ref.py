
import glb
import api.output
import errors   
import requirement

import hashlib

        
class dependent_ref(object):
    """description of class"""
    def __init__(self,part_ref,section,requires):
        errors.SetPartStackFrameInfo()
        self.__part_ref=part_ref
        self.__sectionname=section
        self.__requires=requirement.REQ()|requires
        self.__stackframe=errors.GetPartStackFrameInfo()
        errors.ResetPartStackFrameInfo()
        self.__rsig=None
        self.__rsigs=None
    
    @property
    def StackFrame(self):    
        return self.__stackframe
    
    @property
    def PartRef(self):    
        return self.__part_ref
    
    @property
    def SectionName(self):
        return self.__sectionname
    
    @property
    def Requires(self):
        return self.__requires
    
    @property
    def Part(self):
        try:
            return self.__part
        except AttributeError:            
            if self.__part_ref.hasUniqueMatch:
                self.__part=self.__part_ref.UniqueMatch
            elif self.__part_ref.hasMatch ==False:
                api.output.error_msg(self.NoMatchStr)
            elif self.__part_ref.hasAmbiguousMatch:
                api.output.error_msg(self.AmbiguousMatchStr)
        return self.__part
    
    @property
    def StoredMatchingSections(self):
        
        self.__stored_matches=[]
        matches=self.__part_ref.StoredMatches
        # try to turn matches in to sections
        for m in matches:
            if m.Stored:
                self.__stored_matches.append(m.Stored.sections[self.__sectionname])
            else:
                self.__stored_matches.append(m.Section(self.__sectionname))
        return self.__stored_matches
    
    # clean up the below functions... so we only have one case 
    @property
    def Section(self):
        try:
            return self.__section
        except AttributeError:
            self.__section=self.Part.Section(self.SectionName)
        return self.__section
    
    @property
    def PartSection(self):
        try:
            return self.__part_section
        except AttributeError:
            try:
                self.__part_section=self.Part.Section[self.__section]
            except KeyError:
                api.output.error_msg('Part has no section')
        return self.__part_section
    
    def NoMatchStr(self):
        return "Failed to map dependency because:\n {0}".format(self.__part_ref.NoMatchStr())
    
    def AmbiguousMatchStr(self):
        return "Failed to map dependency because:\n {0}".format(self.__part_ref.AmbiguousMatchStr())

    def rsig(self):
        if self.__rsig is None:
            self._gen_rsigs()
        return self.__rsig        
        
    def rsigs(self):
        if self.__rsigs is None:
            self._gen_rsigs()
        return self.__rsigs

    def _gen_rsigs(self):
        md5_rsig=hashlib.md5()
        rsigs={}
        esigs=self.Section.esigs()
        for req in self.__requires:
            try:
                esig=esigs[req.key]
                md5_rsig.update(esig)
                rsigs[req.key]=esig
            except KeyError:
                pass
        
        self.__rsig=md5_rsig.hexdigest()
        self.__rsigs=rsigs