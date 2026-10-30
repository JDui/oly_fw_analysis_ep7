import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
"""Design tests only. Passing is not E-P7 firmware/allocator qualification."""
import unittest
from dataclasses import FrozenInstanceError, replace
from ep7_inline_job_design import (
    Fixture, Snapshot, Shape, Coefficients, Rejected, STOCK_BYTES,
    EXPANDED_BYTES, shape_for, slot_index,
)


class InlineDesignTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.shape = shape_for(0x10000, 0)
        self.snapshot = Snapshot('capture-A', tuple(range(24)))

    def assert_no_read(self, ticket, shape=None):
        before = self.f.trailer_reads
        with self.assertRaises(Rejected):
            self.f.read_to_coefficients(ticket, shape or self.shape)
        self.assertEqual(self.f.trailer_reads, before)

    def test_all_sixteen_operation_slots(self):
        ticket = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(ticket, self.shape, self.snapshot)
        for slot in range(16):
            shape = shape_for(self.shape.job, slot)
            self.assertEqual(slot_index(shape), slot)
            self.assertEqual(self.f.read_to_coefficients(ticket, shape).values, self.snapshot.values)
        self.assertEqual(self.f.trailer_reads, 16)

    def test_shape_does_not_authorize_unknown_old_failed_uninitialized(self):
        self.assertEqual(slot_index(self.shape), 0)
        self.assert_no_read(object())
        self.assert_no_read(None)
        old = self.f.assume_qualified_allocation(self.shape.job, STOCK_BYTES)
        self.assert_no_read(old)
        with self.assertRaises(Rejected): self.f.initialize(old, self.shape, self.snapshot)
        self.f.release(old)
        failed = self.f.assume_qualified_allocation(self.shape.job, failed=True)
        self.assert_no_read(failed)
        fresh = self.f.assume_qualified_allocation(self.shape.job)
        self.assert_no_read(fresh)

    def test_release_before_read_and_address_reuse_rejected(self):
        old = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(old, self.shape, self.snapshot)
        self.f.release(old)
        self.assert_no_read(old)
        fresh = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(fresh, self.shape, Snapshot('capture-B', (-1,) * 24))
        self.assert_no_read(old)
        self.assertEqual(self.f.read_to_coefficients(fresh, self.shape).values, (-1,) * 24)

    def test_capture_snapshot_not_later_ui_values(self):
        ui = [1] * 24
        first = Snapshot('A', tuple(ui))
        ui[:] = [2] * 24
        second = Snapshot('B', tuple(ui))
        for address, snapshot, value in ((0x10000, first, 1), (0x20000, second, 2)):
            shape = shape_for(address, 3)
            ticket = self.f.assume_qualified_allocation(address)
            self.f.initialize(ticket, shape, snapshot)
            self.assertEqual(self.f.read_to_coefficients(ticket, shape).values, (value,) * 24)
        with self.assertRaises(FrozenInstanceError): first.values = (9,) * 24

    def test_clone_requires_explicit_transfer(self):
        original = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(original, self.shape, self.snapshot)
        clone_shape = shape_for(0x20000, 15)
        clone = self.f.assume_qualified_allocation(clone_shape.job)
        self.assert_no_read(clone, clone_shape)
        self.f.clone_values(original, self.shape, clone, clone_shape)
        self.f.release(original)
        self.assertEqual(self.f.read_to_coefficients(clone, clone_shape).values, self.snapshot.values)
        self.assert_no_read(original)

    def test_scalar_output_survives_job_release_without_pointer_escape(self):
        ticket = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(ticket, self.shape, self.snapshot)
        output = self.f.read_to_coefficients(ticket, self.shape)
        self.f.release(ticket)
        # Simulated hardware may still consume this scalar output, not job H/L.
        self.assertEqual(vars(output), {'values': self.snapshot.values})
        self.assertTrue(all(type(v) is int for v in output.values))
        self.assert_no_read(ticket)

    def test_corrupt_links_external_request_and_penf_stride_rejected(self):
        ticket = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(ticket, self.shape, self.snapshot)
        for shape in (replace(self.shape, request=0x9999), replace(self.shape, callback=0),
                      replace(self.shape, operation_job=0x20000),
                      replace(self.shape, request_operation=0),
                      replace(self.shape, operation_request=0),
                      replace(shape_for(self.shape.job, 1), operation=self.shape.operation+52)):
            self.assert_no_read(ticket, shape)

    def test_no_mutation_reinitialization_or_cross_job_ticket(self):
        ticket = self.f.assume_qualified_allocation(self.shape.job)
        self.f.initialize(ticket, self.shape, self.snapshot)
        with self.assertRaises(Rejected): self.f.initialize(ticket, self.shape, self.snapshot)
        self.assert_no_read(ticket, shape_for(0x20000, 0))

    def test_overlapping_allocation_rejected(self):
        self.f.assume_qualified_allocation(0x10000)
        for address in (0x10004, 0xfffc):
            with self.assertRaises(Rejected):
                self.f.assume_qualified_allocation(address)

    def test_bounds_and_values(self):
        for address, extent in ((0x10001, EXPANDED_BYTES), (2**32-15488, EXPANDED_BYTES),
                                (0, EXPANDED_BYTES), (0x10000, STOCK_BYTES-1)):
            with self.assertRaises(Rejected): self.f.assume_qualified_allocation(address, extent)
        for values in ([0]*24, (0,)*23, (True,)*24, (128,)*24):
            with self.assertRaises(Rejected): Snapshot('A', values)
        for slot in (-1,16,True):
            with self.assertRaises(Rejected): shape_for(self.shape.job, slot)


if __name__ == '__main__': unittest.main()
