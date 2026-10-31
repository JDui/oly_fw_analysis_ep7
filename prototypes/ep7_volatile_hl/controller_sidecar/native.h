#ifndef EP7_CAPTURE_NATIVE_H
#define EP7_CAPTURE_NATIVE_H
#include <stdbool.h>
#include <stdint.h>
bool ep7cn_native_cohort_present(void);
void ep7cn_initialize(unsigned initial);
void ep7cn_fresh(uint32_t node);
void ep7cn_prewrite(uint32_t capture,unsigned postpopulation);
void ep7cn_population(uint32_t node,unsigned finish);
void ep7cn_free(uint32_t node);
void ep7cn_release_capture(uint32_t registry);
void ep7cn_associated_recycle(uint32_t pool,uint32_t header);
void ep7cn_associated_reset(void);
uint32_t ep7cn_wait_enqueue(uint32_t queue,uint32_t associated);
uint32_t ep7cn_wait_pop(uint32_t queue,uint32_t wrapper_sp);
void ep7cn_wait_reset(void);
#endif
