#ifndef EP7_NATIVE_HSL_EDITOR_H
#define EP7_NATIVE_HSL_EDITOR_H
#include <stdbool.h>
#include <stdint.h>

/* PEN-F's single-wheel contract, adapted to E-P7's four COLOR profiles.
 * Native S enums and graphics retain their actual -5..5 range. */
extern unsigned ep7h_axis; /* 0=S, 1=H, 2=L; Delete cycles 0,2,1. */
int ep7h_property(unsigned property);
int ep7h_value(unsigned property,unsigned axis);
int ep7h_set(unsigned property,int value);
int ep7h_cycle(const unsigned char *machine);
bool ep7h_snapshot(unsigned selector,int8_t out[24]);
#endif
