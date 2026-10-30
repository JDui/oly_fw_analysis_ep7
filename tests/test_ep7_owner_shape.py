import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ep7_owner_shape as shape

class ShapeTests(unittest.TestCase):
    def fixture(self,index=0,job=0x62000000):
        request=job+shape.REQUEST_OFFSET
        operation=job+shape.OPERATION_OFFSET+index*shape.OPERATION_STRIDE
        return dict(job=job,request=request,operation=operation,
                    request_callback=shape.CALLBACK,request_operation=operation,
                    operation_job=job,operation_request=request)
    def test_all_sixteen_slots(self):
        for i in range(16):self.assertEqual(shape.embedded_operation_index(**self.fixture(i)),i)
    def test_slot_out_of_bounds(self):
        for i in (-1,16):self.assertIsNone(shape.embedded_operation_index(**self.fixture(i)))
    def test_penf_stride_not_transplanted(self):
        f=self.fixture();f['operation']+=52;f['request_operation']=f['operation']
        self.assertIsNone(shape.embedded_operation_index(**f))
    def test_bad_links_and_callback(self):
        for key in ('request','request_callback','request_operation','operation_job','operation_request'):
            f=self.fixture();f[key]+=4
            self.assertIsNone(shape.embedded_operation_index(**f),key)
    def test_bad_integer_and_wrap(self):
        for value in (None,True,-1,2**32,0,0xfffffff0):
            f=self.fixture();f['job']=value
            self.assertIsNone(shape.embedded_operation_index(**f))
    def test_reuse_is_deliberately_not_detected(self):
        # Same numeric addresses can match twice. This is not a generation lease.
        f=self.fixture(3)
        self.assertEqual(shape.embedded_operation_index(**f),3)
        self.assertEqual(shape.embedded_operation_index(**f),3)

if __name__=='__main__':unittest.main()
