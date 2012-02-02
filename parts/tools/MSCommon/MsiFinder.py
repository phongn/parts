import os
import re
import parts.platformspecific.win32.msi as msi

class MsiFinder(object):
    """
    This class uses MSI API to find tools installed on the system.
    When the objects __call__ method is called the finder reads list
    of apps installed, scans it comparing product name's to specified
    regular expression. When a match is found the code checks whether
    the specified executable is realy on the system and returns
    path to directory where it is installed.
    """
    def __init__(self, productNamePattern, component, upDirs = None):
        """
        @type  productNamePattern: string
        @param productNamePattern: Python RegExp compatilble pattern to match against product name
        @type  component: string
        @param component: String representing MSI database component name of executable of interest.
                          For example, CandleBinaries is component name for candle.exe from Wix package,
                          PythonExe is the name of python.exe component from ActiveState Python package.
        @type  upDirs: integer or None
        @param upDirs: A number of path entries to delete from component path to get install path.
                       Assume upDirs is 2 and path to component is 'foo/bar/bar/component' then path
                       returned by MsiFinder.__call__ will return 'foo/'.
        """
        self.__pattern = re.compile(productNamePattern)
        self.__component = component
        self.__upDirs = upDirs

    def __iter__(self):
        """
        Method to make MsiFinder objects look like sequence type instance.
        """
        yield self
        raise StopIteration

    def __call__(self):
        """
        The method is called by Parts infrastructure to determine whether particular tool is installed
        on the system.
        """
        try:
            return self.__path
        except AttributeError:
            for product in msi.allProducts():
                if self.__pattern.match(product.ProductName):
                    db = msi.Database(product.LocalPackage, msi.MSIDBOPEN_READONLY)
                    view = db.openView("select ComponentId from Component where Component='%s'" \
                            % self.__component)
                    for item in view:
                        state, path = product.getComponentPath(item.valueAsString(1))
                        path = os.path.dirname(path)
                        if state == msi.INSTALLSTATE_LOCAL and os.path.exists(path):
                            if self.__upDirs is not None:
                                for i in xrange(self.__upDirs):
                                    path = os.path.dirname(path)
                            self.__path = path
                            return self.__path
            self.__path = None
        return self.__path

    def resolve(self, version):
        return self()

    def resolve_version(self, version):
        return version



# vim: set et ts=4 sw=4 ft=python :

