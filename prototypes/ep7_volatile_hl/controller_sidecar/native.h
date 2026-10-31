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
#endif
