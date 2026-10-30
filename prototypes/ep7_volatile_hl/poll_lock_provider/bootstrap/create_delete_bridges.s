/* Self-authored GCC callable raw creation/delete veneers, unresolved only. */
.text
.global _ep7_gcc_raw_sem_create
.type _ep7_gcc_raw_sem_create,@function
_ep7_gcc_raw_sem_create:
 movm [a2],(sp)
 add -12,sp
 mov d0,a0
 call ep7_stock_raw_sem_create_unresolved,[d2,a2],16
 ret [a2],16
.size _ep7_gcc_raw_sem_create,.-_ep7_gcc_raw_sem_create
.global _ep7_gcc_raw_sem_delete_unpublished
.type _ep7_gcc_raw_sem_delete_unpublished,@function
_ep7_gcc_raw_sem_delete_unpublished:
 movm [a2],(sp)
 add -12,sp
 call ep7_stock_raw_sem_delete_unresolved,[d2,d3,a2,a3],20
 ret [a2],16
.size _ep7_gcc_raw_sem_delete_unpublished,.-_ep7_gcc_raw_sem_delete_unpublished
