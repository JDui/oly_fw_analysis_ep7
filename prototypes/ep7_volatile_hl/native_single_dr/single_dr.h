#ifndef EP7_SINGLE_DR_H
#define EP7_SINGLE_DR_H

#include <stdint.h>

/* Native build 1100 ordinary still job; the first 24 trailer bytes belong
 * to the existing 015 H/L transport. */
#define EP7DR_JOB_TRAILER 15512u
#define EP7DR_CAPTURE_PENDING 0x40000000u
#define EP7DR_JOB_GAMMA_APPLIED 0x80000000u

/* Read-only pipeline observations for the experimental HDR page.
 * path 0 = live, 1 = capture; stage 0 = sample, 1 = job, 2 = RGB selection. */
void ep7dr_highlight_observe(unsigned path, unsigned stage, uint32_t code);
uint32_t ep7dr_highlight_observation(unsigned path);
void ep7dr_highlight_clear_observations(void);

static inline int ep7dr_fixed_nominal_admissible(int nominal, uint32_t level)
{
    /* Native ISO400/500/640/800 menu codes; no arbitrary Q8 Sv inputs. */
    return (level == 1u && (nominal == 1792 || nominal == 1877 ||
                           nominal == 1962 || nominal == 2048)) ||
           (level == 2u && nominal == 2048);
}

int ep7dr_stage_level(uint32_t public_mode, uint32_t level);
int ep7dr_selected_level(uint32_t public_mode);
int ep7dr_display_level(uint32_t public_mode);
uint32_t ep7dr_settings_blockers(uint32_t public_mode);
int ep7dr_storage_scope(uint32_t public_mode);
enum ep7dr_selection_status {
    EP7DR_SELECTION_AVAILABLE,
    EP7DR_SELECTION_ISO_LOW,
    EP7DR_SELECTION_UNAVAILABLE,
};
enum ep7dr_selection_status ep7dr_selection_status(uint32_t public_mode, uint32_t level);
int ep7dr_stock_key(uint32_t key);
int ep7dr_capture_key(uint32_t capture, uint32_t key);
uint32_t ep7dr_select_scoped_level(uint32_t command, uint32_t engine,
                                  uint32_t *public_mode);
void ep7dr_freeze_plan(uint32_t command, uint32_t engine);
uint32_t ep7dr_plan_for_metadata(uint32_t metadata);
uint32_t ep7dr_record_applied(uint32_t metadata, uint32_t plan);
void ep7dr_reject_plan(uint32_t metadata, uint32_t plan);
uint32_t ep7dr_job_level(uint32_t job);
void ep7dr_job_gamma_applied(uint32_t job);
void ep7dr_job_gamma_clear(uint32_t job);
uint32_t ep7dr_job_gamma_missing(uint32_t job);
uint32_t ep7dr_gamma_schedule_ready(uint32_t job);

#endif
