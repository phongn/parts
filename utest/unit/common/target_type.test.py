import unittest
import SCons.Script
import parts.target_type as target_type
from parts.reporter import PartRuntimeError

class TestParseTarget(unittest.TestCase):

    def setUp(self):
        pass            
        
    def test_parse_concept1(self):
        '''Testing parsing of concept build::'''
        tmp=target_type._parse_target("build::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
    
    def test_parse_concept2(self):
        '''Testing parsing of concept utest::'''
        tmp=target_type._parse_target("utest::")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': True})
        
    def test_parse_concept3(self):
        '''Testing parsing of concept run_utest:: maps to utest::'''
        tmp=target_type._parse_target("run_utest::")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': True})
    
    def test_parse_concept_special1(self):
        '''Testing parsing of concept all'''
        tmp=target_type._parse_target("build::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_parse_concept_special2(self):
        '''Testing parsing of concept name::'''
        tmp=target_type._parse_target("name::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
    
    def test_parse_concept_special3(self):
        '''Testing parsing of concept alias::'''
        tmp=target_type._parse_target("alias::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_parse_concept_special4(self):
        '''Testing parsing of concept alias::::'''
        tmp=target_type._parse_target("alias::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
    
    def test_parse_concept_special5(self):
        '''Testing parsing of concept alias::::'''
        tmp=target_type._parse_target("alias::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_parse_concept_as_implied_name1(self):
        '''Testing parsing of 'concept' build as an name'''
        tmp=target_type._parse_target("build")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'build', 'properties': {}})
        
    def test_parse_concept_as_implied_name2(self):
        '''Testing parsing of 'concept' utest as an name'''
        tmp=target_type._parse_target("utest")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'utest', 'properties': {}})
    
    def test_parse_concept_as_implied_name3(self):
        '''Testing parsing of 'concept' run_utest as an name'''
        tmp=target_type._parse_target("run_utest")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'run_utest', 'properties': {}})
        
    def test_parse_concept_as_implied_name4(self):
        '''Testing parsing of 'concept' alias as an name'''
        tmp=target_type._parse_target("alias")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'alias', 'properties': {}})
        
    def test_parse_concept_as_implied_name5(self):
        '''Testing parsing of 'concept' name as an name'''
        tmp=target_type._parse_target("name")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'name', 'properties': {}})
        
    def test_parse_concept_as_implied_name5(self):
        '''Testing parsing of 'concept' name<properties> as an name'''
        tmp=target_type._parse_target("name@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'name', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})
        
    def test_parse_concept_as_implied_name6(self):
        '''Testing parsing of 'concept' alias<properties> as an name'''
        tmp=target_type._parse_target("alias@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'alias', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})

    def test_parse_alias1(self):
        '''Testing parsing of alias::foo'''
        tmp=target_type._parse_target("alias::foo")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'alias': 'foo'})
        
    def test_parse_alias2(self):
        '''Testing parsing of alias::foo.boo'''
        tmp=target_type._parse_target("alias::foo.boo")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'alias': 'foo.boo'})
        
    def test_parse_alias3(self):
        '''Testing parsing of build::alias::foo'''
        tmp=target_type._parse_target("build::alias::foo")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'alias': 'foo'})
    
    def test_parse_alias4(self):
        '''Testing parsing of utest::alias::foo'''
        tmp=target_type._parse_target("utest::alias::foo")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': False, 'alias': 'foo'})
        
    def test_parse_alias5(self):
        '''Testing parsing of alias::foo::'''
        tmp=target_type._parse_target("alias::foo::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'alias': 'foo'})
        
    def test_parse_alias6(self):
        '''Testing parsing of alias::foo.boo::'''
        tmp=target_type._parse_target("alias::foo.boo::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'alias': 'foo.boo'})
        
    def test_parse_alias7(self):
        '''Testing parsing of build::alias::foo::'''
        tmp=target_type._parse_target("build::alias::foo::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'alias': 'foo'})
    
    def test_parse_alias8(self):
        '''Testing parsing of utest::alias::foo::'''
        tmp=target_type._parse_target("utest::alias::foo::")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': True, 'alias': 'foo'})
        
    def test_parse_name1(self):
        '''Testing parsing of name::foo'''
        tmp=target_type._parse_target("name::foo")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'foo', 'properties': {}})
        
    def test_parse_name2(self):
        '''Testing parsing of name::foo.boo'''
        tmp=target_type._parse_target("name::foo.boo")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'foo.boo', 'properties': {}})
        
    def test_parse_name3(self):
        '''Testing parsing of build::name::foo'''
        tmp=target_type._parse_target("build::name::foo")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'foo', 'properties': {}})
    
    def test_parse_name4(self):
        '''Testing parsing of utest::name::foo'''
        tmp=target_type._parse_target("utest::name::foo")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': False, 'name': 'foo', 'properties': {}})
        
    def test_parse_name5(self):
        '''Testing parsing of utest::foo'''
        tmp=target_type._parse_target("utest::foo")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': False, 'name': 'foo', 'properties': {}})
        
    def test_parse_name6(self):
        '''Testing parsing of name::foo'''
        tmp=target_type._parse_target("name::foo::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'name': 'foo', 'properties': {}})
        
    def test_parse_name7(self):
        '''Testing parsing of name::foo.boo::'''
        tmp=target_type._parse_target("name::foo.boo::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'name': 'foo.boo', 'properties': {}})
        
    def test_parse_name8(self):
        '''Testing parsing of build::name::foo::'''
        tmp=target_type._parse_target("build::name::foo::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'name': 'foo', 'properties': {}})
    
    def test_parse_name8(self):
        '''Testing parsing of utest::name::foo::'''
        tmp=target_type._parse_target("utest::name::foo::")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': True, 'name': 'foo', 'properties': {}})
        
    def test_parse_name10(self):
        '''Testing parsing of utest::foo::'''
        tmp=target_type._parse_target("utest::foo::")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': True, 'name': 'foo', 'properties': {}})
        
    def test_parse_name_properties1(self):
        '''Testing parsing of utest::name::c@k:v@k1:1,2,3,4@k3:hello::'''
        tmp=target_type._parse_target("utest::name::c@k:v@k1:1,2,3,4@k3:hello::")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': True, 'name': 'c', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})
        
    def test_parse_name_properties2(self):
        '''Testing parsing of utest::name::c@k:v@k1:1,2,3,4@k3:hello'''
        tmp=target_type._parse_target("utest::name::c@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp,{'concept': 'utest', 'recurse': False, 'name': 'c', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})

    def test_parse_name_properties3(self):
        '''Testing parsing of name::c@k:v@k1:1,2,3,4@k3:hello::'''
        tmp=target_type._parse_target("build::name::c@k:v@k1:1,2,3,4@k3:hello::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'name': 'c', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})
        
    def test_parse_name_properties4(self):
        '''Testing parsing of name::c@k:v@k1:1,2,3,4@k3:hello'''
        tmp=target_type._parse_target("build::name::c@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'c', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})
        
    def test_parse_name_properties5(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello::'''
        tmp=target_type._parse_target("build::name::c@k:v@k1:1,2,3,4@k3:hello::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'name': 'c', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})
        
    def test_parse_name_properties6(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello'''
        tmp=target_type._parse_target("build::name::c@k:v@k1:1,2,3,4@k3:hello")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'c', 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})

    def test_parse_name_properties7(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3::'''
        tmp=target_type._parse_target("build::name::c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3::")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': True, 'name': 'c', 'groups': ['a1', 'a2', 'b3'], 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})
        
    def test_parse_name_properties8(self):
        '''Testing parsing of c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3'''
        tmp=target_type._parse_target("build::name::c@k:v@k1:1,2,3,4@k3:hello::a1,a2,b3")
        self.assertEqual(tmp,{'concept': 'build', 'recurse': False, 'name': 'c', 'groups': ['a1', 'a2', 'b3'], 'properties': {'k3': 'hello', 'k': 'v', 'k1': ['1', '2', '3']}})

    def test_special1(self):
        '''Testing parsing of utest::::test'''
        tmp=target_type._parse_target("utest::::test")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': False, 'groups': ['test']})
        
    def test_special2(self):
        '''Testing parsing of utest::alias::::test'''
        tmp=target_type._parse_target("utest::alias::::test")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': False, 'groups': ['test']})
        
    def test_special3(self):
        '''Testing parsing of utest::name::::test'''
        tmp=target_type._parse_target("utest::name::::test")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': False, 'groups': ['test']})
        
    def test_special4(self):
        '''Testing parsing of utest::::test::'''
        tmp=target_type._parse_target("utest::::test::")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': True, 'groups': ['test']})
        
    def test_special5(self):
        '''Testing parsing of utest::alias::::test::'''
        tmp=target_type._parse_target("utest::alias::::test::")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': True, 'groups': ['test']})
        
    def test_special6(self):
        '''Testing parsing of utest::name::::test::'''
        tmp=target_type._parse_target("utest::name::::test::")
        self.assertEqual(tmp,{'all': True, 'concept': 'utest', 'recurse': True, 'groups': ['test']})
        
    def test_special7(self):
        '''Testing parsing of build::::'''
        tmp=target_type._parse_target("build::::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_special8(self):
        '''Testing parsing of build::alias::::'''
        tmp=target_type._parse_target("build::alias::::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_special9(self):
        '''Testing parsing of build::name::::'''
        tmp=target_type._parse_target("build::name::::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_special10(self):
        '''Testing parsing of build::::::'''
        tmp=target_type._parse_target("build::::::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_special11(self):
        '''Testing parsing of build::alias::::::'''
        tmp=target_type._parse_target("build::alias::::::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_special12(self):
        '''Testing parsing of build::name::::::'''
        tmp=target_type._parse_target("build::name::::::")
        self.assertEqual(tmp,{'all': True, 'concept': 'build', 'recurse': True})
        
    def test_special_error1(self):
        '''Testing parsing of build::name::n::g:::: exception expected'''
        try:
            tmp=target_type._parse_target("build::name::n::g::::")
        except PartRuntimeError, e:
            self.assertTrue(True)
            return
        self.assertTrue(False)
        
    def test_special_error2(self):
        '''Testing parsing of build:::::::: exception expected'''
        try:
            tmp=target_type._parse_target("build::::::::")
        except PartRuntimeError, e:
            self.assertTrue(True)
            return
        self.assertTrue(False)
        

