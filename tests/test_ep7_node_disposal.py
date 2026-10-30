import unittest, hashlib
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import ep7_node_disposal as m
class Tests(unittest.TestCase):
 def test_exact_guard(self):
  for data in [b'',b'OE',b'not firmware']:
   with self.assertRaisesRegex(ValueError,'wrong exact'):m.inspect(data,m.OBJDUMP)
 @unittest.skipUnless(m.IMAGE.is_file() and m.OBJDUMP.is_file(), "exact proprietary stock and trusted objdump required")
 def test_disassembly_uses_verified_argument_copy(self):
  data=m.IMAGE.read_bytes()
  original=m.subprocess.check_output
  inspected=[]
  def checked(args, **kwargs):
   if "-D" in args:
    path=Path(args[-1])
    self.assertNotEqual(path,m.IMAGE)
    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),hashlib.sha256(data).hexdigest())
    inspected.append(path)
   return original(args,**kwargs)
  with patch.object(m,"IMAGE",Path("/nonexistent-stock-input")), patch.object(m.subprocess,"check_output",side_effect=checked):
   result=m.inspect(data,m.OBJDUMP)
  self.assertEqual(len(inspected),len(m.WINDOWS))
  self.assertFalse(any(p.exists() for p in inspected))
  self.assertEqual(result["checked_instructions"],len(m.W))
 def test_reference_bitmask_model_not_firmware_execution(self):
  for events in [(0x10,0x08),(0x08,0x10)]:
   flags=0;freed=[]
   for bit in events:
    flags|=bit
    if flags&0x18==0x18:freed.append('2a00' if bit==0x10 else '2ab5')
   self.assertEqual(freed,['2a00' if events[-1]==0x10 else '2ab5'])
if __name__=='__main__':unittest.main()
