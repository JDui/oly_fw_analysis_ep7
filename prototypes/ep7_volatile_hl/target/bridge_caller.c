/* Self-authored compile-only caller. No native address and no target execution. */
extern int ep7_gcc_get_tid(unsigned short *);
int ep7_probe_bridge(unsigned short *out) {
    int result=ep7_gcc_get_tid(out);
    return result ? result : (int)*out;
}
