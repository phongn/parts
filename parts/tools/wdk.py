from parts.tools.Common.ToolSetting import ToolSetting
from parts.tools.Common.ToolSetting import MatchVersionNumbers
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import PathFinder
from parts.platform_info import SystemPlatform
import parts.tools.mslink

import SCons.Util
import os

import parts.api.output as output

WDK = ToolSetting('WDK')

hosts = [SystemPlatform('win32', 'any')]
targets = [SystemPlatform('win32', 'any')]

if SCons.Util.can_read_reg:
    def openRegistryKey(key, subkey):
        """
        The problem is that this code may be run on Windows x86 and on Windows Intel64.
        The registry has two branches for HKEY_LOCAL_MACHINE\Software: one is it and
        the other is WOW6432Node.
        The function tries to open the subkey in both branches.

        For info on the magic numbers used in this function look for
        'Accessing an Alternate Registry View' article in
        Microsoft Platform SDK documentation.
        """

        try:
            return SCons.Util.RegOpenKeyEx(key, subkey, 0, SCons.Util.hkey_mod.KEY_READ)
        except:
            pass

        try:
            return SCons.Util.RegOpenKeyEx(key, subkey, 0, SCons.Util.hkey_mod.KEY_READ|0x0100)
        except:
            pass

        try:
            return SCons.Util.RegOpenKeyEx(key, subkey, 0, SCons.Util.hkey_mod.KEY_READ|0x0200)
        except:
            pass

        return None

    def enumRegistryKey(key, i):
        try:
            return SCons.Util.RegEnumKey(key, i)
        except:
            return None
    def readRegistryValue(key, value):
        try:
            return SCons.Util.RegQueryValueEx(key, value)[0]
        except:
            return None

    class WdkScanner:
        # Versions is a dictionary of form {Major0 : {Minor0: {Build0: path}, Minor1: path}}
        versions = None
        plain_versions = None
        def __init(self):
            pass
        def _plainVersions(self):
            def _walkDict(dictionary):
                """ return list of tuples of form ('Major.Minor.Build': 'path') """
                assert type(dictionary) is dict
                res = []
                for key in dictionary.keys():
                    value = dictionary[key]
                    if type(value) is not dict:
                        res.append((str(key), value))
                    else:
                        for tuple in _walkDict(value):
                            res.append(("%s.%s" % (str(key), tuple[0]), tuple[1]))
                return res
            assert WdkScanner.versions is not None
            if WdkScanner.plain_versions is None:
                WdkScanner.plain_versions = _walkDict(WdkScanner.versions)
            return WdkScanner.plain_versions

        def _lookInConfiguredKits(self):
            key = openRegistryKey(SCons.Util.HKEY_LOCAL_MACHINE, r"Software\Microsoft\KitSetup\configured-kits")

            if key is None:
                return None
            for i in range(0,10000):
                s = enumRegistryKey(key, i)
                if s is None:
                    break;

                subkey = openRegistryKey(key, s)
                if subkey is None:
                    continue

                for j in range(0,10000):
                    k = enumRegistryKey(subkey, j)
                    if k is None:
                        break
                    subsubkey = openRegistryKey(subkey, k)
                    if subsubkey is None:
                        continue
                    dir = readRegistryValue(subsubkey, 'setup-install-location')
                    if dir is None:
                        continue
                    dir = os.path.normpath(dir)
                    version = os.path.basename(dir)
                    if version is unicode:
                        version = version.encode('ascii', 'ignore')
                    version = version.split('.')
                    dictionary = WdkScanner.versions
                    for n in range(len(version)-1):
                        if not dictionary.has_key(version[n]):
                            dictionary[version[n]] = {}
                        dictionary = dictionary[version[n]]
                    dictionary[version[-1]] = dir

        def _lookInWinDDK(self):
            key = openRegistryKey(SCons.Util.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\WINDDK")
            if key is not None:
                for i in range(0,10000):
                    s = enumRegistryKey(key, i)
                    if s is None:
                        break
                    k = openRegistryKey(key, s)
                    if k is None:
                        continue
                    dir = readRegistryValue(k, 'LFNDirectory')
                    if dir is None:
                        continue
                    dir = os.path.normpath(dir)
                    version = s
                    if version is unicode:
                        version = version.encode('ascii', 'ignore')
                    version = version.split('.')
                    if len(version) == 0:
                        continue

                    dictionary = WdkScanner.versions
                    for n in range(0,len(version)-1):
                        if not dictionary.has_key(version[n]):
                            dictionary[version[n]] = {}
                        dictionary = dictionary[version[n]]
                    dictionary[version[-1]] = dir

        def scan(self):
            if WdkScanner.versions is None:
                WdkScanner.versions = {}
                self._lookInConfiguredKits()
                self._lookInWinDDK()
            res = {}
            for k,v in self._plainVersions():
                res[k] = os.path.join(v, 'bin')
            return res

        def resolve(self, version):
            res = self.scan()
            for k in res.keys():
                if MatchVersionNumbers(version, k):
                    return res[k]
            return None

        def resolve_version(self, version):
            for k in self.scan().keys():
                if MatchVersionNumbers(version, k):
                    return k
            return None

    def _resolveWdkDir(version):
        try:
            value = WdkScanner.versions
            for v in version.split('.'):
                value = value[v]
            return value
        except:
            return None

    class WdkInfo(ToolInfo):
        def __init__(self):
            ToolInfo.__init__(self, '*', WdkScanner(), False,
                    subst_vars={
                        '_resolveWdkDir': _resolveWdkDir,
                        'DIR': '${WDK._resolveWdkDir(WDK.VERSION)}',
                        'TOOL': 'setenv.bat',
                        },
                    shell_vars={
                        'WDK_DIR':'${WDK.DIR}',
                        'PATH': r'${WDK.DIR}\bin',
                        },
                    test_file='setenv.bat'
                    )
        def version_set(self):
            return set([x for x in self.install_root.scan().keys()])

        def resolve_version(self, version):
            return self.install_root.resolve_version(version)

WDK.Register(hosts=hosts, targets=targets, info=WdkInfo())

def _pdbEmitter(target, source, env):
    extratargets = []
    if env.has_key('PDB') and env['PDB'] and not env.get('IGNORE_PDB', False):
        pdb = env.arg2nodes('$PDB', target = target, source = source)[0]
        extratargets.append(pdb)
        target[0].attributes.pdb = pdb

    return (env.Precious(target + extratargets), env.Precious(source))

def _ddkplatform(platform):
    try:
        return {
            'x86': 'x86',
            'x86_64': 'amd64',
            'ia64': 'ia64',
        }[platform]
    except:
        return platform

def _ddklibplatform(platform):
    try:
        return {
            'x86': 'i386',
            'x86_64': 'amd64',
            'ia64': 'ia64',
        }[platform]
    except:
        return platform

def _resolve_wdk_flags(env, flags):
    min_win_ver = {
        # Windows XP
        'wxp' : 'wxp',
        '5.01': 'wxp',
         5.01 : 'wxp',
         501  : 'wxp',
        # Windows Server 2003
        'wnet': 'wnet',
        '5.02': 'wnet',
         5.02 : 'wnet',
         502  : 'wnet',
        # Windows Vista and Windows Server 2008
        'wlh' : 'wlh',
        '6.00': 'wlh',
         6.00 : 'wlh',
         600  : 'wlh',
        # Windows 7
        'win7' : 'win7',
        '6.01': 'win7',
         6.01 : 'win7',
         601  : 'win7',
    }.get(env.get('DDK_MIN_WIN') or env.get('TARGET_VARIANT')) or 'wxp'
    res = []
    flags = env.get(flags.lower())
    if type(flags) is list:
        for flag in flags:
            if type(flag) == dict:
                try:
                    l = flag[min_win_ver]
                    if type(l) is not list:
                        l = [l]
                    res += l
                except KeyError:
                    pass
    return res

#Actions for DDK stuff
ASAction = SCons.Action.Action("$DDKASCOM", "$DDKASCOMSTR")
CAction = SCons.Action.Action("$DDKCCCOM", "$DDKCCCOMSTR")
CXXAction = SCons.Action.Action("$DDKCXXCOM", "$DDKCXXCOMSTR")

LinkAction = SCons.Action.Action("$DDKLINKCOM", "$DDKLINKCOMSTR")

ASSuffixes = ['.s', '.asm', '.ASM']
CSuffixes = ['.c', '.C']
CXXSuffixes = ['.cc', '.cpp', '.cxx', '.c++', '.C++']

def createDriverBuilder(env):
    try:
        driverBuilder = env['BUILDERS']['WinDriver']
    except KeyError:
        driverBuilder = SCons.Builder.Builder(
            action = LinkAction,
            emitter = '$DDKDRVEMITTER',
            prefix  = '$DDKDRVPREFIX',
            suffix  = '$DDKDRVSUFFIX',
            src_suffix = '$DDKOBJSUFFIX',
            src_builder = 'DriverObject',
            target_scanner = SCons.Tool.ProgramScanner)
        env['BUILDERS']['WinDriver'] = driverBuilder

    return driverBuilder

def createDriverObjectBuilder(env):
    try:
        driverObjectBuilder = env['BUILDERS']['DriverObject']
    except KeyError:
        driverObjectBuilder = SCons.Builder.Builder(
                action = {},
                emiter = {},
                prefix = '$DDKOBJPREFIX', # ''
                suffix = '$DDKOBJSUFFIX', # '.dobj'
                src_builder = ['CFile', 'CXXFile'],
                source_scanner = SCons.Tool.SourceFileScanner,
                single_source = 1)
        env['BUILDERS']['DriverObject'] = driverObjectBuilder

    return driverObjectBuilder

def createBuilders(env):
    return createDriverBuilder(env), createDriverObjectBuilder(env)

def generate(env):
    drvBuilder, drvObjBuilder = createBuilders(env)

    for suffix in ASSuffixes:
        drvObjBuilder.add_action(suffix, ASAction)

    for suffix in CSuffixes:
        drvObjBuilder.add_action(suffix, CAction)

    for suffix in CXXSuffixes:
        drvObjBuilder.add_action(suffix, CXXAction)

    WDK.MergeShellEnv(env)

    env.Append(DDKDRVEMITTER = [_pdbEmitter])
    env['_PDB'] = parts.tools.mslink.pdbGenerator
    env['DDKCCPDBFLAGS'] = SCons.Util.CLVar(['${"/Z7" if PDB else ""}'])
    env['DDKCCPCHFLAGS'] = SCons.Util.CLVar(['${(PCH and "/Yu%s /Fp%s"%(PCHSTOP or "",File(PCH))) or ""}'])

    env['DDK_MIN_WIN'] = 'wnet'

    env['DDKOBJSUFFIX'] = '.dobj'

    env['_ddkplatform'] = _ddkplatform
    env['_ddklibplatform'] = _ddklibplatform
    env['_resolve_wdk_flags'] = _resolve_wdk_flags

    env['DDKDIR'] = r'${WDK.DIR}'
    env['DDKHOSTDIR'] = r'${DDKDIR}\bin\x86'
    env['DDKTARGETARCH'] = r'${_ddkplatform(TARGET_ARCH)}'
    env['DDKHOSTTARGETDIR'] = r'${DDKHOSTDIR}\${DDKTARGETARCH}'

    env['DDKCC'] = env.Detect([r'${DDKHOSTDIR}\cl.exe', r'${DDKHOSTTARGETDIR}\cl.exe'])
    env['DDKLINK'] = env.Detect([r'${DDKHOSTDIR}\link.exe', r'${DDKHOSTTARGETDIR}\link.exe'])
    env['DDKAS'] = env.Detect([r'${DDKHOSTDIR}\ml.exe', r'${DDKHOSTTARGETDIR}\ml.exe']) if env['TARGET_ARCH'] == 'x86' \
        else env.Detect([r'${DDKHOSTTARGETDIR}\ml64.exe'])

    env['_DDKLIBFLAGS'     ] = '${_concat(DDKLIBLINKPREFIX, DDKLIBS, DDKLIBLINKSUFFIX, __env__)}'
    env['_DDKLIBDIRFLAGS'  ] = '$( ${_concat(DDKLIBDIRPREFIX, DDKLIBPATH, DDKLIBDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_DDKCPPINCFLAGS'  ] = '$( ${_concat(DDKINCPREFIX, DDKCPPPATH, DDKINCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_DDKCPPDEFFLAGS'  ] = '${_defines(DDKCPPDEFPREFIX, DDKCPPDEFINES, DDKCPPDEFSUFFIX, __env__)}'

    env['_DDKCPPDEFINES'] = '${_defines(DDKCPPDEFPREFIX, _resolve_wdk_flags(__env__, "_ddkcppdefines"), DDKCPPDEFSUFFIX, __env__)}'
    env['_DDKLIBPATH'] = '$( ${_concat(DDKLIBDIRPREFIX, _resolve_wdk_flags(__env__, "_ddklibpath"), DDKLIBDIRSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_DDKLINKFLAGS'] = '${_resolve_wdk_flags(__env__, "_ddklinkflags")}'
    env['_DDKLIBS'         ] = '${_concat(DDKLIBLINKPREFIX, _resolve_wdk_flags(__env__, "_ddklibs"), DDKLIBLINKSUFFIX, __env__)}'

    env['_DDKCCCOMCOM']  = '$DDKCPPFLAGS $_DDKCPPDEFFLAGS $_DDKCPPDEFINES $_DDKCPPINCFLAGS $DDKCCPCHFLAGS $DDKCCPDBFLAGS'

    env['DDKLIBLINKPREFIX'] = ''
    env['DDKLIBLINKSUFFIX'] = '.lib'
    env['DDKLIBDIRPREFIX']  = '-LIBPATH:'
    env['DDKLIBDIRSUFFIX']  = ''
    env['DDKINCPREFIX'] = '-I'
    env['DDKINCSUFFIX'] = ''
    env['DDKCCCOM']      = '${TEMPFILE("$DDKCC -Fo$TARGET -c $SOURCES $DDKCFLAGS $DDKCCFLAGS $_DDKCCCOMCOM")}'
    env['DDKCPPPATH'] =[r'${DDKDIR}\inc\ddk', r'${DDKDIR}\inc\api', r'${DDKDIR}\inc\crt']
    env['DDKLINKCOM'] = SCons.Action.Action('${TEMPFILE("$DDKLINK $_DDKLIBPATH $_DDKLIBDIRFLAGS $_DDKLINKFLAGS $DDKLINKFLAGS /OUT:$TARGET.windows $_DDKLIBDIRFLAGS $_DDKLIBFLAGS $_DDKLIBS $_PDB $SOURCES.windows")}')
    env['DDKLINKFLAGS'] = []
    env['DDKASCOM']     = '${TEMPFILE("$DDKAS $DDKASFLAGS $_DDKCPPDEFFLAGS $_DDKCPPDEFINES $_DDKCPPINCFLAGS -c -Fo$TARGET $SOURCES")}'

    env['DDKCFLAGS']   = '-nologo'

    env['DDKCXXCOM']     = '${TEMPFILE("$DDKCXX -Fo$TARGET -c $SOURCES $DDKCXXFLAGS $DDKCCFLAGS $_DDKCCCOMCOM")}'
    env['DDKCPPDEFPREFIX']  = '-D'
    env['DDKCPPDEFSUFFIX'] = ''
    env['DDKDRVSUFFIX'] = '.sys'

    # fix this up so we can control its printing to screen better.
    output.print_msg("Configured Tool %s\t for version <%s> target <%s>"%('WDK',env['WDK_VERSION'],env['TARGET_PLATFORM']))

def exists(env):
    return WDK.Exists(env)

