import importlib.util,unittest,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('bridge_check',P/'check.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with tempfile.TemporaryDirectory(prefix='ep7-state-test-') as t:
   m.check(Path(t));cls.dis=(Path(t)/'bridge.local.asm').read_text()
  cls.sections='.text 0000002f '
 def test_good(self):self.assertEqual(m.validate(self.dis,self.sections),17)
 def test_stack(self):self.assertTrue(m.stack_model())
 def test_native_frame(self):
  with self.assertRaises(ValueError):m.validate(self.dis.replace(',[d2,d3,a2,a3],32',',[d2,d3,a2,a3],16'),self.sections)
 def test_scratch(self):
  with self.assertRaises(ValueError):m.validate(self.dis.replace('-32,sp','-16,sp'),self.sections)
 def test_flush_overlap(self):
  with self.assertRaises(ValueError):m.validate(self.dis.replace('d0,(12,sp)','d0,(8,sp)'),self.sections)
 def test_return(self):
  with self.assertRaises(ValueError):m.validate(self.dis.replace('ret\t[d2,d3,a2,a3],32','ret\t[d2,d3,a2,a3],64'),self.sections)
 def test_gcc_frame(self):
  with self.assertRaises(ValueError):m.validate(self.dis.replace(',[],0',',[],4'),self.sections)
 def test_target(self):
  with self.assertRaises(ValueError):m.validate(self.dis.replace('ep7_stock_state_service_unresolved+0x1','ep7_wrong_unresolved+0x1'),self.sections)
 def test_size(self):
  with self.assertRaises(ValueError):m.validate(self.dis,'.text 00000030 ')
if __name__=='__main__':unittest.main()
