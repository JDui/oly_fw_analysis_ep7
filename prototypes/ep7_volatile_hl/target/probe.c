/* Self-authored ABI probes: compile only, never linked or executed. */
typedef unsigned short u16;
unsigned probe_integer(unsigned x,unsigned y) { return x+y; }
void *probe_pointer(void *p) { return p; }
unsigned probe_load(const unsigned *p,unsigned x) { return *p+x; }
void probe_store(unsigned *p,unsigned x,unsigned y) { *p=x+y; }
unsigned probe_four(unsigned a,unsigned b,unsigned c,unsigned d) { return a+b+c+d; }
unsigned probe_div(unsigned a,unsigned b) { return a/b; }
extern int foreign_query_unresolved(u16 *);
int probe_query(u16 *p) { int r=foreign_query_unresolved(p); return r ? r : *p; }
extern unsigned foreign_mix_unresolved(unsigned,void *,unsigned);
unsigned probe_nonleaf(unsigned x,void *p,unsigned y) {
 unsigned r=foreign_mix_unresolved(x,p,y);
 return r+x+y+*(unsigned *)p;
}
extern void *foreign_pointer_unresolved(unsigned);
unsigned probe_pointer_call(unsigned x) { return *(unsigned *)foreign_pointer_unresolved(x); }
