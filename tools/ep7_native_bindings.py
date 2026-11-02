"""Reviewed build1100 native addresses; these are bindings, not placement approval.

Names are ELF names. GCC C objects receive an initial underscore; the assembly
bridges deliberately use native entry names without it. A pointer_cell binding
is the address of the cell, never the pointer currently stored in that cell.
Evidence paths refer to existing native investigations, not to fresh executions.
"""


def legacy_bindings():
    rows = {}

    def add(kind, evidence, values):
        for name, address in values.items():
            symbol = ('_' if kind not in ('function', 'continuation') else '')+'ep7_stock_'+name+'_unresolved'
            if symbol in rows:
                raise ValueError('duplicate native binding '+symbol)
            rows[symbol] = dict(address=address, kind=kind, evidence='tools/'+evidence+'.py')

    add('function', 'ep7_capture_native_binding', dict(
        capture_fresh=0x602a3116, capture_lookup=0x6029b9d1,
        capture_node_free=0x60022732, capture_pool_release=0x603db89e,
        capture_population=0x602a7ea0, capture_postpopulation=0x602a8dbd,
        state_service=0x6028a882))
    add('function', 'ep7_associated_pool', dict(
        associated_enqueue=0x6020b98b, associated_initialize=0x602972aa))
    add('function', 'ep7_deferred_producer', dict(
        wait_initialize=0x6020b949, wait_pop=0x6020b9ff, wait_service=0x602ac5d0))
    add('function', 'ep7_engine_epoch', dict(engine_configure=0x6029ad23, engine_pool=0x6029acd8))
    add('function', 'ep7_producer_scope', dict(
        kind19_metadata_producer=0x602ac748, command_send=0x6020beb4,
        queue_send_preserving=0x600514b6))
    add('function', 'ep7_worker_scope', dict(
        job_allocate=0x60022700, worker_cleanup=0x603e6c8d,
        worker_job=0x603f2800, worker_process=0x603e61b8))
    add('function', 'ep7_ack_frames', dict(ack=0x603df97d))
    add('function', 'ep7_descriptor_receive_frames', dict(receive_wrapper=0x603eeb57))
    add('function', 'ep7_descriptor_send_frames', dict(send_wrapper=0x603eeba4))
    # 60036caf is the index-check analysis window, not a callable entry: it
    # skips saving destination/timeout and the native dispatch-context check.
    add('function', 'ep7_queue_transport', dict(
        queue_receive_local=0x60036c8e, queue_send_local=0x60036ede))
    add('function', 'ep7_semaphore_bootstrap', dict(raw_sem_create=0x6003057f, raw_sem_delete=0x60031107))
    add('function', 'ep7_private_semaphore', dict(raw_sem_signal=0x60035b62, raw_sem_wait=0x600370af))
    add('function', 'ep7_current_task_stack', dict(get_tid=0x600317ac))
    add('function', 'ep7_cleanup_delay', dict(task_delay=0x600313ef))
    add('function', 'ep7_remaining_far_calls', dict(color_builder=0x603b0068))
    add('function', 'ep7_bootstrap_entry', dict(bootstrap_original=0x6011f620))
    add('function', 'ep7_candidate_boot_guard_sim', dict(terminal_af=0x601e73e5))
    add('continuation', 'ep7_capture_native_binding', dict(capture_init_continue=0x602897dd))
    add('continuation', 'ep7_queue_kernel_gate', dict(
        delete_gate_continue=0x60031078, receive_gate_continue=0x60036d46,
        receive_gate_error=0x60036e17, send_gate_continue=0x60036f99, send_gate_error=0x600370a3))

    add('function', 'ep7_native_hsl', dict(
        h_active_get=0x602cc0a7,
        h_active_set=0x602cc0d0,
        h_raw_get=0x602afa81,
        h_manager=0x60827440,
        h_manager_finish=0x608274b3,
        h_get=0x607f9549,
        h_default=0x607f964a,
        h_descriptor=0x60d115c2,
        h_dispatch_resume=0x60d11463,
        h_viewer=0x60e26ab0,
        h_gui_root=0x60d3379b,
        h_root_invalidate=0x60d00ef1,
        h_draw=0x60ea250b,
        h_initial_resume=0x60d7ad2f,
        h_changed_resume=0x60d7adb9,
        h_update=0x60d7ae23,
        h_invalidate=0x60cfe266,
        h_paint=0x60d02f93,
        h_pen=0x60d0fc05,
        h_brush=0x60d0f9c2,
        h_rectangle=0x60d0c227,
        h_font=0x60d0fce0,
        h_font_release=0x60d10708,
        h_text=0x60d075a7))
    return rows


def bindings():
    from ep7_native_transport import bindings as transport_bindings
    from ep7_native_live import bindings as live_bindings
    rows={name:row for name,row in legacy_bindings().items() if name.startswith('ep7_stock_h_')}
    for name,address in transport_bindings().items():
        if name in rows:raise ValueError('duplicate native transport binding '+name)
        rows[name]=dict(address=address,kind='function',evidence='tools/ep7_native_transport.py')
    for name,address in live_bindings().items():
        if name in rows:raise ValueError('duplicate native live binding '+name)
        rows[name]=dict(address=address,kind='function',evidence='tools/ep7_native_live.py')
    return rows
