import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
from dataclasses import replace
import ep7_scoped_admission_design as d
from ep7_inline_job_design import Snapshot, shape_for, EXPANDED_BYTES, STOCK_BYTES

class Tests(unittest.TestCase):
    def setUp(self):
        self.f=d.ScopedAdmission();self.task=self.f.assume_task_instance(7)
        self.shape=shape_for(0x10000,3);self.ticket=self.alloc(self.shape,1)
        self.current=d.CurrentRequest(0,11,0,0)
    def alloc(self,shape,value):
        t=self.f.allocations.assume_qualified_allocation(shape.job)
        self.f.allocations.initialize(t,shape,Snapshot('synthetic', (value,)*24));return t
    def read(self,handle,**kw):
        return self.f.read(kw.get('task',self.task),handle,kw.get('ticket',self.ticket),kw.get('shape',self.shape),kw.get('current',self.current))
    def reject_no_read(self,fn):
        before=self.f.allocations.trailer_reads
        with self.assertRaises(d.Rejected):fn()
        self.assertEqual(before,self.f.allocations.trailer_reads)
    def test_normal_admission(self):
        with self.f.scope(self.task,self.ticket,self.shape) as h:
            self.assertEqual(self.read(h).values,(1,)*24)
        self.assertEqual(self.f.allocations.trailer_reads,1)
        self.reject_no_read(lambda:self.read(h))
    def test_interleaved_tasks_are_isolated(self):
        other=self.f.assume_task_instance(8);s=shape_for(0x20000,0);t=self.alloc(s,2)
        with self.f.scope(self.task,self.ticket,self.shape) as a:
            with self.f.scope(other,t,s) as b:
                self.reject_no_read(lambda:self.read(a,task=other))
                self.reject_no_read(lambda:self.read(b))
                self.assertEqual(self.f.read(other,b,t,s,self.current).values,(2,)*24)
                self.assertEqual(self.read(a).values,(1,)*24)
    def test_nested_mismatch_and_lifo(self):
        s=shape_for(0x20000,1);t=self.alloc(s,2)
        with self.f.scope(self.task,self.ticket,self.shape) as outer:
            with self.f.scope(self.task,t,s) as inner:
                self.reject_no_read(lambda:self.read(outer))
                self.reject_no_read(lambda:self.read(inner))
                with self.assertRaises(d.Rejected):self.f.leave(self.task,outer)
                self.assertEqual(self.f.read(self.task,inner,t,s,self.current).values,(2,)*24)
            self.assertEqual(self.read(outer).values,(1,)*24)
    def test_exception_cleanup_and_old_scope(self):
        with self.assertRaises(RuntimeError):
            with self.f.scope(self.task,self.ticket,self.shape) as h:raise RuntimeError('synthetic')
        self.reject_no_read(lambda:self.read(h))
        with self.f.scope(self.task,self.ticket,self.shape) as fresh:self.read(fresh)
    def test_allocation_reuse_rejects_old_ticket(self):
        with self.f.scope(self.task,self.ticket,self.shape) as h:
            self.f.allocations.release(self.ticket);new=self.alloc(self.shape,2)
            self.reject_no_read(lambda:self.read(h))
            self.reject_no_read(lambda:self.read(h,ticket=new))
    def test_numeric_task_id_reuse_requires_new_instance(self):
        old=self.f.enter(self.task,self.ticket,self.shape)
        self.f.revoke_task(self.task);new=self.f.assume_task_instance(7)
        self.reject_no_read(lambda:self.read(old))
        self.reject_no_read(lambda:self.read(old,task=new))
        self.reject_no_read(lambda:self.read(old,task=7))
        with self.f.scope(new,self.ticket,self.shape) as h:self.read(h,task=new)
    def test_current_gates_rechecked_before_read(self):
        with self.f.scope(self.task,self.ticket,self.shape) as h:
            for field,value in [('request_type',1),('raw_mode',12),('owner',1),('mutation_callback',0x1234),('request_type',False)]:
                self.reject_no_read(lambda:self.read(h,current=replace(self.current,**{field:value})))
            self.read(h)
    def test_stage_and_embedded_shape_gates(self):
        for stage in ({'stage_index':1},{'stage_callback':0x6036884e},{'stage_index':True}):
            self.reject_no_read(lambda:self.f.enter(self.task,self.ticket,self.shape,**stage))
        self.reject_no_read(lambda:self.f.enter(self.task,self.ticket,replace(self.shape,request=self.shape.request+4)))
    def test_shape_never_mints_allocation_provenance(self):
        forged=object()
        with self.f.scope(self.task,forged,self.shape) as h:
            self.reject_no_read(lambda:self.f.read(self.task,h,forged,self.shape,self.current))
        s=shape_for(0x20000,0);t=self.f.allocations.assume_qualified_allocation(s.job,STOCK_BYTES)
        with self.f.scope(self.task,t,s) as h:
            self.reject_no_read(lambda:self.f.read(self.task,h,t,s,self.current))
    def test_revoke_cleans_nested_scopes_and_contextmanagers(self):
        with self.f.scope(self.task,self.ticket,self.shape) as outer:
            with self.f.scope(self.task,self.ticket,self.shape) as inner:
                self.f.revoke_task(self.task)
                self.reject_no_read(lambda:self.read(inner))
        self.reject_no_read(lambda:self.read(outer))
    def test_task_id_width_and_model_task_capacity(self):
        f=d.ScopedAdmission(max_tasks=2)
        zero=f.assume_task_instance(0);f.assume_task_instance(65535)
        for tid in (-1,65536,True,1.0):
            with self.assertRaises(d.Rejected):f.assume_task_instance(tid)
        with self.assertRaises(d.Rejected):f.assume_task_instance(1)
        self.assertEqual(len(f._live_ids),2)
        f.revoke_task(zero);f.assume_task_instance(1)
    def test_model_depth_overflow_does_not_push(self):
        f=d.ScopedAdmission(self.f.allocations,max_depth=1);task=f.assume_task_instance(0)
        with f.scope(task,self.ticket,self.shape) as outer:
            with self.assertRaises(d.Rejected):f.enter(task,self.ticket,self.shape)
            self.assertEqual(len(f._tasks[task].stack),1)
            f.read(task,outer,self.ticket,self.shape,self.current)
        for kw in ({'max_tasks':0},{'max_depth':-1},{'max_depth':True}):
            with self.assertRaises(d.Rejected):d.ScopedAdmission(**kw)
    def test_abnormal_unwind_revokes_unclosed_manual_descendants(self):
        with self.assertRaisesRegex(RuntimeError,'original'):
            with self.f.scope(self.task,self.ticket,self.shape) as outer:
                inner=self.f.enter(self.task,self.ticket,self.shape)
                deepest=self.f.enter(self.task,self.ticket,self.shape)
                raise RuntimeError('original')
        for h in (outer,inner,deepest):self.reject_no_read(lambda:self.read(h))
        self.assertEqual(self.f._tasks[self.task].stack,[])
        with self.f.scope(self.task,self.ticket,self.shape) as fresh:self.read(fresh)
    def test_corrupt_missing_stack_frame_revokes_task_preserves_exception(self):
        with self.assertRaisesRegex(RuntimeError,'original'):
            with self.f.scope(self.task,self.ticket,self.shape) as outer:
                inner=self.f.enter(self.task,self.ticket,self.shape)
                self.f._tasks[self.task].stack.remove(outer)
                raise RuntimeError('original')
        for h in (outer,inner):self.reject_no_read(lambda:self.read(h))
        self.assertNotIn(self.task,self.f._tasks)
        self.assertEqual(self.f._scopes,{})
        self.f.assume_task_instance(7)
    def test_missing_both_frame_and_stack_entry_revokes_task(self):
        with self.assertRaisesRegex(RuntimeError, 'original'):
            with self.f.scope(self.task, self.ticket, self.shape) as outer:
                inner = self.f.enter(self.task, self.ticket, self.shape)
                del self.f._scopes[outer]
                self.f._tasks[self.task].stack.remove(outer)
                raise RuntimeError('original')
        for handle in (outer, inner):
            self.reject_no_read(lambda: self.read(handle))
        self.assertNotIn(self.task, self.f._tasks)
        self.assertEqual(self.f._scopes, {})

    def test_explicit_manual_leave_is_not_corruption(self):
        with self.f.scope(self.task, self.ticket, self.shape) as outer:
            self.f.leave(self.task, outer)
            new_scope = self.f.enter(self.task, self.ticket, self.shape)
        self.assertEqual(self.read(new_scope).values, (1,) * 24)
        self.f.leave(self.task, new_scope)
        self.reject_no_read(lambda: self.read(outer))

    def test_dead_frames_and_tasks_reclaimed(self):
        for _ in range(100):
            with self.f.scope(self.task,self.ticket,self.shape):pass
        self.assertEqual(self.f._scopes,{})
        self.f.revoke_task(self.task)
        self.assertEqual(self.f._tasks,{})
if __name__=='__main__':unittest.main()
