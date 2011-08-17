import unittest
from parts.pickle_helpers import *
import SCons.Node
import os

class TestPickleHelpers(unittest.TestCase):
    __rootDirName = "."

    def __createEntry(self, fName, dirName):
        fs = SCons.Node.FS.get_default_fs()
        return SCons.Node.FS.Entry(fName, self.__createDir(dirName), fs)

    def __createFile(self, fName, dirName):
        fs = SCons.Node.FS.get_default_fs()
        return SCons.Node.FS.File(fName, self.__createDir(dirName), fs)

    def __createDir(self, dirName):
        rootDir = SCons.Node.FS.RootDir(self.__rootDirName, SCons.Node.FS.get_default_fs())
        return SCons.Node.FS.Dir(dirName, rootDir, SCons.Node.FS.get_default_fs())

    def setUp(self):
        pass

    def test_node_to_str(self):
        """Test that nodes are correctly represented as strings"""
        entName = "entry.txt"
        dir1Name = "directory1"
        dir2Name = "directory2"
        dir3Name = "directory3"
        dirName = dir1Name + os.sep + dir2Name + os.sep + dir3Name
        fileName = "file.txt"
        valueName = "value1"
        aliasName = "alias1"

        entry = self.__createEntry(entName, dirName)
        strRepresentation1 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name + "/" + entName
        self.assertEqual(node_to_str(entry), strRepresentation1)

        _dir = self.__createDir(dirName)
        strRepresentation2 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name
        self.assertEqual(node_to_str(_dir), strRepresentation2)

        _file = self.__createFile(fileName, dirName)
        strRepresentation3 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name + "/" + fileName
        self.assertEqual(node_to_str(_file), strRepresentation3)

        value = SCons.Node.Python.Value(valueName)
        self.assertEqual(node_to_str(value), valueName)

        alias = SCons.Node.Alias.Alias(aliasName)
        self.assertEqual(node_to_str(alias), aliasName)
        #TODO: test string node

    def test_node_typestr(self):
        """Test that type of node is correctly converted to string"""
        entName = "entry.txt"
        dir1Name = "directory1"
        dir2Name = "directory2"
        dir3Name = "directory3"
        dirName = dir1Name + os.sep + dir2Name + os.sep + dir3Name
        fileName = "file.txt"
        valueName = "value1"
        aliasName = "alias1"

        entry = self.__createEntry(entName, dirName)
        self.assertEqual(node_typestr(entry), "Entry")

        _dir = self.__createDir(dirName)
        self.assertEqual(node_typestr(_dir), "Dir")

        _file = self.__createFile(fileName, dirName)
        self.assertEqual(node_typestr(_file), "File")

        value = SCons.Node.Python.Value(valueName)
        self.assertEqual(node_typestr(value), "Value")

        alias = SCons.Node.Alias.Alias(aliasName)
        self.assertEqual(node_typestr(alias), "Alias")
        #TODO: string node

    def test_node_type(self):
        """Test that type of node is correctly deternimed by its string representation"""
        self.assertEqual(node_type("File"), SCons.Node.FS.File)
        self.assertEqual(node_type("Dir"), SCons.Node.FS.Dir)
        self.assertEqual(node_type("Entry"), SCons.Node.FS.Entry)
        self.assertEqual(node_type("Value"), SCons.Node.Python.Value)
        self.assertEqual(node_type("Alias"), SCons.Node.Alias.Alias)

    def test_pickle_node(self):
        """Test that node is pickled correctly"""
        entName = "entry.txt"
        rootDirName = "./"
        dir1Name = "directory1"
        dir2Name = "directory2"
        dir3Name = "directory3"
        dirName = dir1Name + os.sep + dir2Name + os.sep + dir3Name
        fileName = "file.txt"
        valueName = "value1"
        aliasName = "alias1"

        entry = self.__createEntry(entName, dirName)
        strRepresentation1 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name + "/" + entName
        self.assertEqual(pickle_node(entry), "Entry::" + strRepresentation1)

        _dir = self.__createDir(dirName)
        strRepresentation2 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name
        self.assertEqual(pickle_node(_dir), "Dir::" + strRepresentation2)

        _file = self.__createFile(fileName, dirName)
        strRepresentation3 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name + "/" + fileName
        self.assertEqual(pickle_node(_file), "File::" + strRepresentation3)

        value = SCons.Node.Python.Value(valueName)
        self.assertEqual(pickle_node(value), "Value::" + valueName)

        alias = SCons.Node.Alias.Alias(aliasName)
        self.assertEqual(pickle_node(alias), "Alias::" + aliasName)
        #TODO: test string node

    def test_unpickle_node(self):
        """Test that node is unpickled correctly"""
        entName = "entry.txt"
        rootDirName = "./"
        dir1Name = "directory1"
        dir2Name = "directory2"
        dir3Name = "directory3"
        dirName = dir1Name + os.sep + dir2Name + os.sep + dir3Name
        fileName = "file.txt"
        valueName = "value1"
        aliasName = "alias1"

        entry = self.__createEntry(entName, dirName)
        strRepresentation1 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name + "/" + entName
        self.assertEqual(isinstance(unpickle_node("Entry::" + strRepresentation1), SCons.Node.FS.Entry), True)

        _dir = self.__createDir(dirName)
        strRepresentation2 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name
        self.assertEqual(isinstance(unpickle_node("Dir::" + strRepresentation2), SCons.Node.FS.Dir), True)

        _file = self.__createFile(fileName, dirName)
        strRepresentation3 = self.__rootDirName + "/" + dir1Name + "/" + dir2Name + "/" + dir3Name + "/" + fileName
        self.assertEqual(isinstance(unpickle_node("File::" + strRepresentation3), SCons.Node.FS.File), True)

        value = SCons.Node.Python.Value(valueName)
        self.assertEqual(isinstance(unpickle_node("Value::" + valueName), SCons.Node.Python.Value), True)

        alias = SCons.Node.Alias.Alias(aliasName)
        self.assertEqual(isinstance(unpickle_node("Alias::" + aliasName), SCons.Node.Alias.Alias), True)
        #TODO: test string node

    def test_pickle_unpickle_req(self):
        """Test that requirement is correctly pickled/unpickled"""
        req1 = requirement.requirement("key1")
        req2 = requirement.requirement("key2", internal = True, public = True, weight = 1)
        sampleReq = requirement.REQ([req1, req2], 2)
        pickledStr = pickle_req(sampleReq)
        unpickledReq = unpickle_req(pickledStr)
        self.assertEqual(str(sampleReq), str(unpickledReq))

    def test_persistent_pickle_unpickle(self):
        """Test that the following stuff is pickled/ unpickled correctly: node, req"""
        entName = "entry.txt"
        rootDirName = "./"
        dir1Name = "directory1"
        dir2Name = "directory2"
        dir3Name = "directory3"
        dirName = dir1Name + os.sep + dir2Name + os.sep + dir3Name
        fileName = "file.txt"
        valueName = "value1"
        aliasName = "alias1"
        req1 = requirement.requirement("key1")
        req2 = requirement.requirement("key2", internal = True, public = True, weight = 1)

        entry = self.__createEntry(entName, dirName)
        _dir = self.__createDir(dirName)
        _file = self.__createFile(fileName, dirName)
        value = SCons.Node.Python.Value(valueName)
        alias = SCons.Node.Alias.Alias(aliasName)
        req = requirement.REQ([req1, req2], 2)

        for item in (req, entry, _dir, _file, value, alias):
            self.assertEqual(str(persistent_unpickle(persistent_pickle(item))), str(item))

    def test_persistent_id_load(self):
        """Test that the following stuff is pickled to/ unpicked from persistent id: node"""
        entName = "entry.txt"
        rootDirName = "./"
        dir1Name = "directory1"
        dir2Name = "directory2"
        dir3Name = "directory3"
        dirName = dir1Name + os.sep + dir2Name + os.sep + dir3Name
        fileName = "file.txt"
        valueName = "value1"
        aliasName = "alias1"

        entry = self.__createEntry(entName, dirName)
        _dir = self.__createDir(dirName)
        _file = self.__createFile(fileName, dirName)
        value = SCons.Node.Python.Value(valueName)
        alias = SCons.Node.Alias.Alias(aliasName)

        for item in (entry, _dir, _file, value, alias):
            self.assertEqual(str(persistent_load(persistent_id(item))), str(item))
