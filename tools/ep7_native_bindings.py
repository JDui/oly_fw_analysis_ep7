"""Reviewed build1100 native addresses; these are bindings, not placement approval.

Names are ELF names. GCC C objects receive an initial underscore; the assembly
bridges deliberately use native entry names without it. A pointer_cell binding
is the address of the cell, never the pointer currently stored in that cell.
Evidence paths refer to existing native investigations, not to fresh executions.
"""


def bindings():
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

    add('function', 'ep7_ui_mvc_lifetime', dict(
        mvc_gui_entry=0x60e5dae9, mvc_gui_exit=0x60e5db01,
        mvc_parent_destroy=0x60e26130, mvc_viewer_destroy=0x60e26a7c))
    add('function', 'ep7_ui_content_rebuild', dict(
        mvc_array_delete=0x60a4ec21, mvc_array_new=0x60a4ec0d,
        mvc_scalar_delete=0x60a4ec17, mvc_scalar_new=0x60a4ec03,
        mvc_base_destroy=0x60dd50d8, mvc_base_init=0x60dd5083, mvc_rebuild=0x60e266a9))
    add('function', 'ep7_ui_color_gate', dict(
        mvc_creator0=0x60de33a7, mvc_creator14=0x60df002e, mvc_creator7=0x60e2054e,
        mvc_stock_selected=0x60e26795, mvc_stop535=0x60dd5857, ui_timer_cancel=0x60ea15ca))
    add('function', 'ep7_ui_viewer_join', dict(mvc_viewer_draw=0x60e26ab0, property_service=0x607f9062))
    add('function', 'ep7_ui_owner_binding', dict(
        screen_manager=0x60d37b53, ui_owner_bulk=0x60d42d69,
        ui_owner_cleanup=0x60d43d4b, ui_owner_destructor=0x60d7ab79))
    add('function', 'ep7_ui_selector_storage', dict(selector_init=0x60de150c))
    add('function', 'ep7_text_native_lifecycle', dict(
        text_bind=0x60d0487a, text_cleanup=0x60d048d0, text_destructor=0x60d4be64,
        text_setter=0x60d4c9df, ui_attach=0x60d02beb, ui_find_child=0x60d02cc2))
    add('function', 'ep7_ui_context_binding', dict(
        ui_context_get=0x60cfe58f, ui_context_set=0x60cfe586, ui_service=0x60d3379b))
    add('function', 'ep7_ui_input_binding', dict(
        ui_dispatch=0x60d1144d, ui_drop_event=0x60d1050a, ui_event=0x60dd5250,
        ui_preprocess=0x60e9fa88, ui_wheel_set=0x60ea3b2c))
    add('function', 'ep7_ui_screen_activation', dict(widget_factory=0x60d337b2))

    add('pointer_cell', 'ep7_ui_input_binding', dict(
        color_container=0x61fc436c, gui_machine=0x61fb2564, ui_repeat_context=0x61fc3808))
    add('mutable_word', 'ep7_ui_color_gate', dict(
        ui_active_content=0x61fc1ba8, ui_input_gate=0x61fc1bac))
    add('mutable_halfword', 'ep7_ui_color_gate', dict(selector_remembered=0x61fc26ae))
    add('function_pointer_cell', 'ep7_ui_mvc_lifetime', dict(
        gui_color_entry=0x611a3b50, gui_color_exit=0x611a3bc4))
    add('function_pointer_cell', 'ep7_ui_selector_storage', dict(selector_initializer=0x6114f334))
    add('table_address', 'ep7_ui_owner_binding', dict(
        ui_service_vtable=0x60faaab4, ui_display_vtable=0x61032f10))
    add('table_address', 'ep7_ui_mvc_lifetime', dict(
        mvc_parent_vtable=0x6118957c, mvc_viewer_vtable=0x61189ba8))
    add('table_address', 'ep7_ui_color_gate', dict(mvc_category_keys=0x61189278))
    add('resource_address', 'ep7_ui_resource_origin', dict(
        hl_text_descriptor=0x61032ea8, hl_text_layouts=0x61031b84))
    add('instruction_address', 'ep7_remaining_far_calls', dict(
        mvc_rebuild_initial_call=0x60e261d4, mvc_rebuild_previous_call=0x60e26201,
        mvc_rebuild_next_call=0x60e26226, mvc_rebuild_touch_call=0x60e269f0,
        ui_wheel_0_call=0x60ea00f7, ui_wheel_1_call=0x60ea0070,
        ui_wheel_2_call=0x60ea0d70, ui_wheel_3_call=0x60ea0e66, ui_wheel_4_call=0x60ea0deb))
    add('instruction_address', 'ep7_ui_input_binding', dict(
        ui_preprocess_call=0x60cfd53a, ui_dispatch_call=0x60cfd558))
    # Private storage is a linker-owned, image-initialized section. It no longer
    # consumes a native pool slot or references a prefix clear continuation.
    return rows
