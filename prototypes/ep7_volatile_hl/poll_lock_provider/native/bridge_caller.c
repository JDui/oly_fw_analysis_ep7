/* Compile-only scalar argument / nonleaf preservation probe. */
extern int ep7_gcc_raw_sem_poll(unsigned int);
extern int ep7_gcc_raw_sem_signal(unsigned int);
int ep7_raw_pair_probe(unsigned int handle){
 int s=ep7_gcc_raw_sem_poll(handle);
 if(s!=0)return s;
 return ep7_gcc_raw_sem_signal(handle);
}
