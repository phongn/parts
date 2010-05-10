import unittest
import SCons.Script
from parts.platform_info import *
from parts.parts import *


class TestPlatform(unittest.TestCase):

    def setUp(self):
        self.env=core.generate_config({},{},{}) 

    def test_platform1(self):
        s1 = SystemPlatform('win32','x86_64')
        self.assertEqual(s1,'win32-x86_64')
        
    def test_platform2(self):
        s1 = SystemPlatform('any','x86')
        self.assertEqual(s1,'any-x86')

    def test_platform3(self):
        s1 = SystemPlatform('win32','x86_64')
        s2 = SystemPlatform('win32','x86_64')
        self.assertTrue(s1 == s2)

    def test_platform4(self):
        s1 = SystemPlatform('win32','x86_64')
        s2 = SystemPlatform('win32','any')
        self.assertTrue(s1 == s2)
        
    def test_platform5(self):
        s1 = SystemPlatform('win32','x86_64')
        s2 = SystemPlatform('any','x86_64')
        self.assertTrue(s1 == s2)
        
    def test_platform6(self):
        s1 = SystemPlatform('win32','x86_64')
        s2 = SystemPlatform('any','any')
        self.assertTrue(s1 == s2)
        
    def test_platform7(self):
        s1 = SystemPlatform('x86','win32')
        s2 = SystemPlatform('win32','x86')
        self.assertFalse(s1 == s2)

    def test_platform8(self):
        s1 = SystemPlatform('x86','win32')
        s2 = SystemPlatform('win32','x86')
        self.assertTrue(s1 != s2)

    def test_platform9(self):
        s1 = SystemPlatform('x86','win32')
        s2 = SystemPlatform('win32','x86')
        self.assertTrue(s1 == s2)
        
    def test_platform10(self):        
        s1 = SystemPlatform('win32','x86')
        self.assertEqual(s1['OS'],'win32')        
        
    def test_platform11(self):        
        s1 = SystemPlatform('win32','x86')
        self.assertEqual(s1['ARCH'],'x86')                
        
    def test_platform12(self):        
        s1 = SystemPlatform('win32','x86')
        s1['ARCH'] = 'x86_64'
        self.assertEqual(s1,'win32-x86_64')

    def test_platform13(self):        
        s1 = SystemPlatform('win32','x86')
        s2 = s1;
        self.assertEqual(s2,'win32-x86')

    def test_platform14(self):        
        s1 = SystemPlatform('win32','x86')
        s2 = s1.__deepcopy__();
        self.assertEqual(s2,'win32-x86')

    def test_platform15(self):        
        s1 = SystemPlatform('win32','x86')        
        self.assertEqual(s1._getOS(),'win32')        
        
    def test_platform16(self):        
        s1 = SystemPlatform('win32','x86')        
        self.assertEqual(s1._getArch(),'x86') 

    def test_platform17(self):
        try:
            s1 = SystemPlatform('foo','bar')
        except PartRuntimeError, e:
            self.assertTrue(False)
            return
        self.assertTrue(True)        