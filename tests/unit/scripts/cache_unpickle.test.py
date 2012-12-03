import os

import parts.glb as glb
import parts.pnode as pnode
import unittest
from scripts.cache_unpickle import *

cachesDir = './testdata/caches'

class Test_zip_package1(unittest.TestCase):
    def setUp(self):
        self.__cacheRoorDir = os.path.abspath(os.path.join(cachesDir, 'zip_package1'))
        self.__cacheNodeinfoDir = os.path.join(self.__cacheRoorDir, '.parts.cache', '549cbc09859b0735fb41556c809b6af7')
        self.__nodeinfoFilepath = os.path.join(self.__cacheNodeinfoDir, 'nodeinfo.cache')
        self.__globaldataFilepath = os.path.join(self.__cacheNodeinfoDir, 'global_data.cache')
        self.__partmapFilepath = os.path.join(self.__cacheNodeinfoDir, 'part_map.cache')

    def test_split(self):
        '''Test splitting of cache path'''
        (cacheRootDir, cacheDirName, cacheKey, cacheName) = split(self.__nodeinfoFilepath)

        self.assertEqual(cacheRootDir, self.__cacheRoorDir)
        self.assertEqual(cacheDirName, '.parts.cache')
        self.assertEqual(cacheKey, '549cbc09859b0735fb41556c809b6af7')
        self.assertEqual(cacheName, 'nodeinfo')

    def test_unpickle_nodeinfo(self):
        '''Test unpickling of nodeinfo.cache'''
        # When unpickling Part objects they are added to glb.pnodes thus damaging it
        # with unexpected data. Save the copy of glb.pnodes, unpickle data and restore
        # glb.pnodes back then
        pnodesOrig = glb.pnodes
        glb.pnodes = pnode.pnode_manager.manager()

        unpickledNodeinfo = unpickle(self.__nodeinfoFilepath)
        self.assertEqual(type(unpickledNodeinfo), dict)

        expectedRootKeys = [NodeinfoKeys.KNOWN_PNODES, NodeinfoKeys.KNOWN_NODES, NodeinfoKeys.ALIASES]
        self.assertEqual(sorted(expectedRootKeys), sorted(unpickledNodeinfo.keys()))

        knownPnodesDict = unpickledNodeinfo[NodeinfoKeys.KNOWN_PNODES]
        self.assertEqual(type(knownPnodesDict), dict)
        expectedPnodeKeys = ['build::zip_package1_alias', 'build::zip_package2_alias', 'zip_package1_alias', 'zip_package2_alias']
        self.assertEqual(sorted(expectedPnodeKeys), sorted(knownPnodesDict.keys()))

        knownNodesDict = unpickledNodeinfo[NodeinfoKeys.KNOWN_NODES]
        self.assertEqual(type(knownNodesDict), dict)
        self.assertTrue('test1.cpp' in knownNodesDict.keys())
        self.assertTrue('test2.cpp' in knownNodesDict.keys())

        knownAliasesDict = unpickledNodeinfo[NodeinfoKeys.ALIASES]
        self.assertEqual(type(knownAliasesDict), dict)
        self.assertTrue('build::' in knownAliasesDict.keys())

        glb.pnodes = pnodesOrig

    def test_unpickle_global_data(self):
        '''Test unpickling of global_data.cache'''
        unpickledGlobaldata = unpickle(self.__globaldataFilepath)
        self.assertEqual(type(unpickledGlobaldata), dict)

        expectedRootKeys = ['sconstruct_files']
        self.assertEqual(sorted(expectedRootKeys), sorted(unpickledGlobaldata.keys()))

    def test_unpickle_part_map(self):
        '''Test unpickling of part_map.cache'''
        # See comment in "test_unpickle_nodeinfo"
        pnodesOrig = glb.pnodes
        glb.pnodes = pnode.pnode_manager.manager()

        unpickledPartmap = unpickle(self.__partmapFilepath)
        self.assertEqual(type(unpickledPartmap), dict)

        expectedRootKeys = ['__version__' ] + [PartMapKeys.HAS_CLASSIC, PartMapKeys.KNOWN_PARTS, PartMapKeys.NAME_TO_ALIAS]
        self.assertEqual(sorted(expectedRootKeys), sorted(unpickledPartmap.keys()))

        knownPartsDict = unpickledPartmap[PartMapKeys.KNOWN_PARTS]
        self.assertEqual(type(knownPartsDict), dict)
        self.assertTrue('zip_package1_alias' in knownPartsDict.keys())
        self.assertTrue('zip_package2_alias' in knownPartsDict.keys())

        knownNameToAliasDict = unpickledPartmap[PartMapKeys.NAME_TO_ALIAS]
        self.assertEqual(type(knownNameToAliasDict), dict)
        self.assertTrue('zip_package1' in knownNameToAliasDict.keys())
        self.assertTrue('zip_package2' in knownNameToAliasDict.keys())

        glb.pnodes = pnodesOrig

    def test_NodeinfoParser(self):
        '''Test that NodeinfoParser API works correctly with nodeinfo.cache'''
        # See comment in "test_unpickle_nodeinfo"
        pnodesOrig = glb.pnodes
        glb.pnodes = pnode.pnode_manager.manager()

        nodeinfoParser = NodeinfoParser(self.__nodeinfoFilepath)
        aliases = nodeinfoParser.getAliases()
        expectedPnodeKeys = ['zip_package1_alias', 'zip_package2_alias']
        self.assertEqual(sorted(expectedPnodeKeys), sorted(aliases))

        self.assertEqual(set(['build']), nodeinfoParser.getSectionNames('zip_package1_alias'))
        self.assertEqual(set(['build']), nodeinfoParser.getSectionNames('zip_package2_alias'))

        self.assertTrue('test1.cpp' in [x[0] for x in nodeinfoParser.getNodes('zip_package1_alias', existingOnly = False)])
        self.assertTrue('test2.cpp' in [x[0] for x in nodeinfoParser.getNodes('zip_package2_alias', existingOnly = False)])

        glb.pnodes = pnodesOrig

class Test_checkout1(unittest.TestCase):
    # We are testing only vcs cache here because nodeinfo, global_data and part_map
    # stuff was tested above
    def setUp(self):
        self.__cacheRoorDir = os.path.abspath(os.path.join(cachesDir, 'checkout1'))
        self.__cacheVcsDir = os.path.join(self.__cacheRoorDir, '.parts.cache', 'vcs')
        self.__compbarFilepath = os.path.join(self.__cacheVcsDir, 'compbar_alias.cache')
        self.__compfooFilepath = os.path.join(self.__cacheVcsDir, 'compfoo_alias.cache')

    def test_unpickle_vcs(self):
        '''Test unpickling of vcs/*.cache files'''
        unpickledCompbar = unpickle(self.__compbarFilepath)
        self.assertEqual(type(unpickledCompbar), dict)

        expectedRootKeys = ['__version__' ] + [VcsKeys.COMPLETED, VcsKeys.TYPE, VcsKeys.SERVER]
        self.assertEqual(sorted(expectedRootKeys), sorted(unpickledCompbar.keys()))

        self.assertEqual(unpickledCompbar[VcsKeys.TYPE], 'svn')
        self.assertTrue(unpickledCompbar[VcsKeys.SERVER].endswith(r'compbar/static/compbar_0.0.1'))

        unpickledCompfoo = unpickle(self.__compfooFilepath)
        self.assertEqual(type(unpickledCompfoo), dict)

        expectedRootKeys = ['__version__' ] + [VcsKeys.COMPLETED, VcsKeys.TYPE, VcsKeys.SERVER]
        self.assertEqual(sorted(expectedRootKeys), sorted(unpickledCompfoo.keys()))

        self.assertEqual(unpickledCompfoo[VcsKeys.TYPE], 'svn')
        self.assertTrue(unpickledCompfoo[VcsKeys.SERVER].endswith(r'compfoo/base/mainline/compfoo1'))
