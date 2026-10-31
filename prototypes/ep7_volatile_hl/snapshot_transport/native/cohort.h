#ifndef EP7_PIPELINE_NATIVE_COHORT_H
#define EP7_PIPELINE_NATIVE_COHORT_H
#include <stdbool.h>
/* Actual instruction/configuration comparison. Requires all referenced code and
 * tables resident. A future cold installer must require this BEFORE publication;
 * this alone does not qualify placement, task lifetime or hardware visibility. */
bool ep7q_native_cohort_present(void);
#endif
