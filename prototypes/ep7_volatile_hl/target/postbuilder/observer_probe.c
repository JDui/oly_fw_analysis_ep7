/* No camera memory read. Forces GCC nonleaf envelope and setup forwarding.
 * Real scoped admission/decoder/output callback remains unbound. */
extern void ep7_observer_sink_unresolved(void *, unsigned);
void ep7_gcc_postbuilder_observer_unresolved(void *setup) {
    ep7_observer_sink_unresolved(setup,1u);
    ep7_observer_sink_unresolved(setup,2u);
}
