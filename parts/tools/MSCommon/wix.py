"""
The file contains WiX tool stuff which we want to be in single instance.
This file is not loaded by SCons.Tool() call it is called with Python
import technique so its uniqueness is supported by python.
"""
import SCons.Scanner
import SCons.Builder
import SCons.Tool
import SCons.Node.FS
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

def findIncludes(wxsFileNode):
    document = xml.dom.minidom.parseString(wxsFileNode.get_contents())

    def _scanNode(node):
        for child in node.childNodes:
            if child.nodeType == xml.dom.minidom.Node.PROCESSING_INSTRUCTION_NODE \
                    and child.nodeName == 'include':
                yield child.data
            for item in _scanNode(child):
                yield item

    for item in _scanNode(document):
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
    includes = []
    for include in findIncludes(node):
        foundFile = SCons.Node.FS.find_file(include, path)
        if foundFile is not None:
            includes.append(foundFile)
        else:
            includes.append(include)
    return includes

def wixObjScanner(node, env, path):
    """
    This function should return a list of file nodes changes in those
    lead to changes in resulting .msi.
    """
    # The node is .wixobj file. We cannot rely on it because its format is
    # undocumented and is the subject to change. Instead we get the first node's
    # child which is .wxs and have well documented format.
    result = []
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
    SCons.Scanner.Scanner(wixSrcScanner)
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

