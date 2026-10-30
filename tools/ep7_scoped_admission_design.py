"""Single-threaded host simulation; NOT native TLS, task discovery, or a patch.

An explicitly assumed task-instance token is distinct from a numeric task ID.
Native task creation/exit/reuse, TLS, allocation qualification, capture coherence,
and concurrency remain unresolved. No firmware, device, or memory API is used.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from ep7_inline_job_design import Fixture, Rejected, Shape, slot_index

NORMAL_STAGE_INDEX = 2
NORMAL_STAGE_CALLBACK = 0x6036884D


@dataclass(frozen=True)
class CurrentRequest:
    request_type: int
    raw_mode: int
    owner: int
    mutation_callback: int

    def admit(self):
        # Exact values and types; booleans are not native integer observations.
        if any(type(v) is not int for v in vars(self).values()):
            raise Rejected('integer observations required')
        if (self.request_type, self.raw_mode, self.owner, self.mutation_callback) != (0, 11, 0, 0):
            raise Rejected('unsupported current request')


@dataclass
class _Task:
    numeric_id: int
    stack: list = field(default_factory=list)
    live: bool = True


@dataclass
class _Scope:
    task: object
    ticket: object
    shape: Shape
    live: bool = True


class ScopedAdmission:
    """Tickets and task tokens are independent explicit simulation assumptions.

    Interleaving below is manually ordered, not actual concurrent execution.
    `CurrentRequest` is supplied anew at read time, not cached on scope entry.
    """
    def __init__(self, allocations=None, *, max_tasks=16, max_depth=8):
        # Explicit model resource budgets; these are NOT native capacities.
        if any(type(n) is not int or n <= 0 for n in (max_tasks, max_depth)):
            raise Rejected("positive model capacities required")
        self.max_tasks = max_tasks
        self.max_depth = max_depth
        self.allocations = allocations if allocations is not None else Fixture()
        self._tasks = {}
        self._live_ids = {}
        self._scopes = {}

    def assume_task_instance(self, numeric_id):
        if type(numeric_id) is not int or not 0 <= numeric_id <= 65535 or numeric_id in self._live_ids:
            raise Rejected('new explicit task instance required')
        if len(self._live_ids) >= self.max_tasks:
            raise Rejected('model task capacity exceeded')
        token = object()
        self._tasks[token] = _Task(numeric_id)
        self._live_ids[numeric_id] = token
        return token

    def _task(self, token):
        task = self._tasks.get(token) if type(token) is object else None
        if task is None or not task.live or self._live_ids.get(task.numeric_id) is not token:
            raise Rejected('live assumed task-instance token required; numeric ID is insufficient')
        return task

    def _revoke_unchecked(self, token):
        # Cleanup must also find frames lost from a malformed task stack.
        for handle, scope in list(self._scopes.items()):
            if scope.task is token:
                scope.live = False
                del self._scopes[handle]
        task = self._tasks.pop(token, None)
        if task is not None:
            task.stack = []
            task.live = False
            if self._live_ids.get(task.numeric_id) is token:
                del self._live_ids[task.numeric_id]

    def revoke_task(self, token):
        self._task(token)
        self._revoke_unchecked(token)

    def enter(self, task_token, ticket, shape, *, stage_index=2, stage_callback=NORMAL_STAGE_CALLBACK):
        task = self._task(task_token)
        if (type(stage_index) is not int or stage_index != NORMAL_STAGE_INDEX or
                type(stage_callback) is not int or stage_callback != NORMAL_STAGE_CALLBACK):
            raise Rejected('normal stage only')
        slot_index(shape)  # Embedded geometry check is not allocation provenance.
        if type(ticket) is not object:
            raise Rejected('independent allocation ticket required')
        if len(task.stack) >= self.max_depth:
            raise Rejected('model nesting capacity exceeded')
        handle = object()
        self._scopes[handle] = _Scope(task_token, ticket, shape)
        task.stack.append(handle)
        return handle

    def _top(self, task_token, handle):
        task = self._task(task_token)
        scope = self._scopes.get(handle) if type(handle) is object else None
        if (scope is None or not scope.live or scope.task is not task_token or
                not task.stack or task.stack[-1] is not handle):
            raise Rejected('matching live top scope required')
        return task, scope

    def leave(self, task_token, handle):
        task, scope = self._top(task_token, handle)
        task.stack.pop()
        scope.live = False
        del self._scopes[handle]

    @contextmanager
    def scope(self, task_token, ticket, shape, **stage):
        handle = self.enter(task_token, ticket, shape, **stage)
        owned_frame = self._scopes[handle]
        try:
            yield handle
        finally:
            # Explicit revocation / manual leave may already have removed it.
            scope = self._scopes.get(handle)
            if scope is None:
                task = self._tasks.get(task_token)
                if task is not None and (owned_frame.live or
                        type(task.stack) is not list or handle in task.stack):
                    self._revoke_unchecked(task_token)
            else:
                task = self._tasks.get(task_token)
                valid = (task is not None and task.live and
                         self._live_ids.get(task.numeric_id) is task_token and
                         type(task.stack) is list and
                         task.stack.count(handle) == 1 and
                         all(type(h) is object and h in self._scopes and
                             self._scopes[h].task is task_token
                             for h in task.stack))
                if not valid:
                    # Missing/corrupt bookkeeping: invalidate the entire task;
                    # never mask an exception already propagating from the body.
                    self._revoke_unchecked(task_token)
                else:
                    index = task.stack.index(handle)
                    for descendant in task.stack[index:]:
                        self._scopes[descendant].live = False
                        self._scopes.pop(descendant, None)
                    del task.stack[index:]

    def read(self, task_token, handle, ticket, shape, current):
        _, scope = self._top(task_token, handle)
        if ticket is not scope.ticket or shape != scope.shape:
            raise Rejected('nested context/allocation mismatch')
        if type(current) is not CurrentRequest:
            raise Rejected('fresh current request observations required')
        current.admit()
        slot_index(shape)
        # Only this call can count as a trailer read; it independently validates
        # ticket liveness, exact extent, address reuse and initialized snapshot.
        return self.allocations.read_to_coefficients(ticket, shape)
