#include "ep7_ui_adapter_contract.h"
_Static_assert(sizeof(((struct ep7_ui_frame *)0)->logical_steps) / sizeof(int16_t) == 12, "twelve sectors");
int ep7_contract_compiles(const struct ep7_ui_adapter_ops *ops) { return ops != NULL; }
