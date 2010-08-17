import sys
win32=sys.platform == 'win32'

import unittest
from parts.version import *
import SCons.Script

class TestVersionObject(unittest.TestCase):

    def setUp(self):
        pass


    def test_version_major(self):
        "Testing major() call"
        v=version(2.9)
        self.assertEqual(v.major(),2)

    def test_version_pattern_2(self):
        '''Testing minor() call'''
        v=version(2.9,4)
        self.assertEqual(v.minor(),9)
        
    def test_version_pattern_3(self):
        '''Testing revision() call'''
        v=version(2.9,4)
        self.assertEqual(v.revision(),4)

    def test_version_pattern_4(self):
        '''Testing Major() call'''
        v=version("2.9.4")
        self.assertEqual(v.Major(),'2')

    def test_version_pattern_5(self):
        '''Testing Minor() call'''
        v=version("2.9.4")
        self.assertEqual(v.Minor(),'9')   

    def test_version_pattern_6(self):
        '''Testing Revision() call'''
        v=version("2.9.4")
        self.assertEqual(v.Revision(),'4')

    def test_version_pattern_7(self):
        '''Testing version(2.9.3) in version(2.9.0)-version(2.9.4)'''
        v1=version("2.9.0")
        v2=version("2.9.4")
        self.assertTrue("2.9.3" in v1-v2)
        
    def test_version_pattern_8(self):
        '''Testing version(2.9.5) in version(2.9.0)-version(2.9.4)'''
        v1=version("2.9.0")
        v2=version("2.9.4")
        self.assertFalse("2.9.5" in v1-v2)         

    def test_version_pattern_9(self):
        '''Testing version(2.9.4.3) in version(2.9.4.0)-version(2.9.4.1)'''
        v1=version("2.9.4.0")
        v2=version("2.9.4.1")
        self.assertFalse("2.9.4.3" in v1-v2)

    def test_version_pattern_9a(self):
        '''Testing version(2.9.4.3) in version(2.9.4.0)-version(2.9.4.5)'''
        v1=version("2.9.4.0")
        v2=version("2.9.4.5")
        self.assertTrue("2.9.4.3" in v1-v2)          

    def test_version_pattern_10(self):
        '''Testing version(2.9.0)<version(2.9.4)'''
        v1=version("2.9.0")
        v2=version("2.9.4")
        self.assertTrue(v1<v2)

    def test_version_pattern_11(self):
        '''Testing version(2.10.0)<version(2.9.4)'''
        v1=version("2.10.0")
        v2=version("2.9.4")
        self.assertFalse(v1<v2)      

    def test_version_pattern_12(self):
        '''Testing version(2.10.0)>version(2.9.4)'''
        v1=version("2.10.0")
        v2=version("2.9.4")
        self.assertTrue(v1>v2)

    def test_version_pattern_13(self):
        '''Testing version(3.1.0)<version(2.9.4)'''
        v1=version("3.1.0")
        v2=version("2.9.4")
        self.assertFalse(v1<v2)

    def test_version_pattern_14(self):
        '''Testing version(2.9.4)<version(2.9.4)'''
        v1=version("2.9.4")
        v2=version("2.9.4")
        self.assertFalse(v1<v2)

    def test_version_pattern_15(self):
        '''Testing version(2.9.4)>version(2.9.4)'''
        v1=version("2.9.4")
        v2=version("2.9.4")
        self.assertFalse(v1>v2)
        
    def test_version_pattern_16(self):
        v1=version("2.9.4")
        v2=version("2.9.4")
        self.assertTrue(v1>=v2)
        
    def test_version_pattern_17(self):
        v1=version("2.9.4")
        v2=version("2.9.5")
        self.assertFalse(v1>=v2)
        
    def test_version_pattern_18(self):
        v1=version("2.9.4")
        v2=version("2.9.4")
        self.assertTrue(v1<=v2)
    
    def test_version_pattern_19(self):
        v1=version("2.9.4")
        v2=version("2.9.4")
        self.assertTrue(v1<=v2)        
        
    def test_version_pattern_20(self):
        v1=version("2.9.3")
        v2=version("2.9.4")
        self.assertTrue(v1<=v2)        

    def test_version_pattern_21(self):
        v1=version("2.9.4")
        v2=version("2.9.3")
        self.assertFalse(v1<=v2)

    def test_version_pattern_22(self):
        v1=version("2.9.4")
        v2=version(v1)
        self.assertEqual(v2.Revision(),'4')
        
    def test_version_pattern_23(self):
        v1=version('2.2.09063011')
        v2=version("2.2.10")
        self.assertFalse(v1<=v2)       
        
    def test_version_pattern_24(self):
        v1=version("2.9.6")
        v2=version("2.9.5")
        self.assertTrue(v1>=v2)        
        
        