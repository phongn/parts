
import os
import tarfile
import zipfile

import tester
import gtest.host as host

class ZipContent(tester.Tester):
    def __init__(self,zfile, includes = None, excludes=None, kill_on_failure=False):

        # validate we can process the file.
        fileName = zfile.lower()
        if not(fileName.endswith('.tar.gz') or fileName.endswith('.tgz') or fileName.endswith('.tar.bz2') \
            or fileName.endswith('.tbz') or fileName.endswith('.tb2') or fileName.endswith('.zip') or fileName.endswith('.bz2')):
            host.WriteError('Unsupported archive extension for zip file {0}\n Support extension are:\n'+\
            ' .zip,\n  .tb2,\n  .tar.gz,\n  .tgz,\n  .tar.bz2,\n  .bz2,\n  .tb2'.format(zfile))

        super(ZipContent,self).__init__(test_value=True,kill_on_failure=kill_on_failure)
        self.Description="Checking that {0} contains {1} and does not contain {2}".format(zfile,includes,excludes)
        self.zfile=zfile
        self.include=includes
        self.excludes=excludes

    def test(self,eventinfo, **kw):
        fileName = self.__fromFile.name.lower()
        if fileName.endswith('.tar.gz') or fileName.endswith('.tgz') or fileName.endswith('.tar.bz2') \
            or fileName.endswith('.tbz') or fileName.endswith('.tb2') or fileName.endswith('.bz2'):
            archive = tarfile.open(self.zipfile)
            names = archive.getnames()
        elif fileName.endswith('.zip'):
            archive = zipfile.ZipFile(self.zipfile)
            names = archive.namelist()
        

        if self.__contains:
            for contain in self.__contains:
                if contain not in names:
                    self.Result=ResultType.Failed
                    reason='File "{0}" not found in archive "{}"'.format(contain,self.zfile)
                    if self.KillOnFailure:
                        self.Reason=reason+"\n Kill on failure is set".format(val,self._value)
                        raise KillOnFailureError
                    self.Reason=reason
                    

        if self.__notContains:
            for notContain in self.__notContains:
                if notContain in names:
                    self.Result=ResultType.Failed
                    reason='File "{0}" found in archive "{}"'.format(contain,self.zfile)
                    if self.KillOnFailure:
                        self.Reason=reason+"\n Kill on failure is set".format(val,self._value)
                        raise KillOnFailureError
                    self.Reason=reason

        self.Result=ResultType.Passed
        self.Reason="Archive file contents match requested filters"
