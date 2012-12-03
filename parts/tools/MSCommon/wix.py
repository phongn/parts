"""
The file contains WiX tool stuff which we want to be in single instance.
This file is not loaded by SCons.Tool() call it is called with Python
import technique so its uniqueness is supported by python.
"""
import os
import re
import SCons.Scanner
import SCons.Builder
import SCons.Tool
import SCons.Node.FS
import SCons.Util
import xml.dom.minidom
from parts.platform_info import SystemPlatform
from parts.tools.Common.ToolSetting import ToolSetting
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import PathFinder
from parts.tools.Common.Finders import EnvFinder
from parts.tools.MSCommon.MsiFinder import MsiFinder

wix = ToolSetting('WIX')

wix.Register(
    hosts = [SystemPlatform('win32', 'any')],
    targets = [SystemPlatform('win32', 'any')],
    info = [
        ToolInfo(
            version='3.5',
            install_scanner=[
                MsiFinder(
                    r'Windows Installer XML.*',
                    r'CandleBinaries'
                    ),
                PathFinder([
                    r'c:\Program Files (x86)\Windows Installer XML v3.5\bin'
                ]),
                EnvFinder([
                    'PATH'
                ], '.')
            ],
            script=False,
            subst_vars={},
            shell_vars={
                'PATH': '${WIX.INSTALL_ROOT}'
                },
            test_file='candle.exe'
            )
        ]
    )

import SCons.Subst

class WixPreprocessor(object):
    class SysVars(object):
        __slots__ = ['__init__', 'CURRENTDIR', 'SOURCEFILEPATH', 'SOURCEFILEDIR', 'PLATFORM']

        def __init__(self, cwd, source, platform):
            self.CURRENTDIR = cwd
            self.SOURCEFILEPATH = source
            self.SOURCEFILEDIR = os.path.dirname(source) + os.path.sep
            self.PLATFORM = platform

    class EnvVars(object):
        __slots__ = ['__init__', 'mydict', '__getattribute__']
        def __init__(self, adict):
            self.mydict = adict

        def __getattribute__(self, name):
            return object.__getattribute__(self, 'mydict')[name]

    class VarVars(object):
        def __init__(self, vars):
            for var in vars:
                defs = re.match('^(?P<name>[^=]+)=(?P<value>.*)$', var)
                if defs:
                    self.__dict__[defs.groupdict()['name']] = defs.groupdict()['value']

        def define(self, name, value):
            self.__dict__[name] = value

        def __getattribute__(self, name):
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                return ''

    def __init__(self, env, source, env2var=None):
        self.__env = env
        self.__lvars = {
            'var': self.__class__.VarVars(SCons.Util.flatten(self.__env.get(env2var, []))),
            'env': self.__class__.EnvVars(self.__env['ENV']),
            'sys': self.__class__.SysVars(self.__env.Dir('.'), str(source), 'Intel')
        }
        self.__sources = [source]

    def define(self, name, value):
        if re.match('^[\'"].*[\'"]$', value):
            value = value[1:-1]
        self.__lvars['var'].define(name, value)

    def subst(self, strsubst):
        return SCons.Subst.scons_subst(strsubst, self.__env, lvars=self.__lvars)

    def push(self, source):
        self.__sources.append(source)

    def pop(self):
        return self.__sources.pop()

def findIncludes(wxsFileNode, preprocessor, path):
    """
    The function returns iterator by files included in specified wxs/wxi file.
    """
    document = xml.dom.minidom.parseString(wxsFileNode.get_contents())

    def _scanNode(node, preprocessor, path=path):
        """
        Recursive iterator by included files.
        """
        for child in node.childNodes:
            if child.nodeType == xml.dom.minidom.Node.PROCESSING_INSTRUCTION_NODE:
                if child.nodeName == 'include':
                    include = preprocessor.subst(re.sub(r'\$\(((env|var|sys)\.([^\)]+))\)', r'${\1}', child.data.strip()))
                    foundFile = SCons.Node.FS.find_file(include, tuple([x for x in path] + [wxsFileNode.dir]))
                    if foundFile is not None:
                        yield foundFile
                        preprocessor.push(foundFile)
                        for childFile in findIncludes(foundFile, preprocessor, path):
                            yield childFile
                        preprocessor.pop()
                    else:
                        yield include
                elif child.nodeName == 'define':
                    define = re.match(r'(?P<name>[^=\s]+)(\s*=\s*(?P<value>\S+)?)?', child.data.strip()).groupdict()
                    if define:
                        preprocessor.define(define['name'], define.get('value', ''))
            for item in _scanNode(child, preprocessor):
                yield item

    for item in _scanNode(document, preprocessor):
        yield item
                
def getFilesFromWxs(node, elementTagName = 'File', attributeName = 'Source'):
    """
    Returns a list of string representing files referenced by the specified node.

    @param node: SCons.Node.Node descender representing the node.
    """
    document = xml.dom.minidom.parseString(node.get_contents())

    for element in document.getElementsByTagName(elementTagName):
        srcName = element.getAttribute(attributeName)
        if srcName is not None and srcName != "":
            yield srcName

def wixSrcScanner(node, env, path):
    """
    Returns list of files changes in those leads to changes in .wixobj's content.
    """
    if len(path) == 0:
        path = (node.dir,)
    if not node.rexists():
        return []
    includes = []
    preprocessor = WixPreprocessor(env, node.abspath, 'WIXPPDEFINES')

    return [include for include in findIncludes(node, preprocessor, path)]

def wixObjScanner(node, env, path):
    """
    This function should return a list of file nodes changes in those
    lead to changes in resulting .msi.
    """
    # The node is .wixobj file. We cannot rely on it because its format is
    # undocumented and is the subject to change. Instead we get the first node's
    # child which is .wxs and have well documented format.
    result = []
    if not node.children()[0].rexists():
        return result

    if len(path) == 0:
        path = (node.dir,)

    for file in getFilesFromWxs(node.children()[0]):
        foundFile = SCons.Node.FS.find_file(file, path)
        if foundFile:
            result.append(foundFile)
        else:
            result.append(file)
    return result

SCons.Tool.SourceFileScanner.add_scanner(
    '.wixobj',
    SCons.Scanner.Scanner(
        wixObjScanner,
        path_function=SCons.Scanner.FindPathDirs('WIXFILEPATH')
    )
)

SCons.Tool.SourceFileScanner.add_scanner(
    '.wxs', 
    SCons.Scanner.Scanner(
        wixSrcScanner,
        path_function=SCons.Scanner.FindPathDirs('WIXPPPATH')
    )
)

def createWixObjectBuilder(env):
    """
    The function adds WixObject builder to the environment.
    """
    try:
        result = env['BUILDERS']['WixObject']
    except KeyError:
        result = SCons.Builder.Builder(
                action = '$WIXCLCOM',
                emitter = {},
                prefix = '$WIXOBJPREFIX',
                suffix = '$WIXOBJSUFFIX',
                src_suffix = '.wxs',
                single_source = 1,
                source_scanner = SCons.Tool.SourceFileScanner,
                )
        env['BUILDERS']['WixObject'] = result

    return result

def createMsiBuilder(env):
    """
    Adds MSI builder to the environment.
    """
    try:
        result = env['BUILDERS']['MSI']
    except KeyError:
        result = SCons.Builder.Builder(
                action = '$WIXLINKCOM',
                emitter = {},
                prefix = '$MSIPREFIX',
                suffix = '$MSISUFFIX',
                src_suffix = '$WIXOBJSUFFIX',
                src_builder = 'WixObject',
                source_scanner = SCons.Tool.SourceFileScanner,
                )
        env['BUILDERS']['MSI'] = result

    return result


# vim: set et ts=4 sw=4 ft=python :

