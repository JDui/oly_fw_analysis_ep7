/* Normalized host/UI adapter; no native addresses are called or patched. */
#include "ep7p_ui.h"
#include <string.h>

static int profile(uint16_t mode) {
    switch(mode) { case 54:return 0; case 55:return 1; case 56:return 2; case 64:return 3; default:return -1; }
}
static bool supported(uint16_t mode,uint8_t category) {
    return profile(mode)>=0 && (category==4 || category==5);
}
static ep7p_ui_slot *lookup(ep7p_ui *ui,struct ep7_ui_session session) {
    ep7p_ui_slot *slot;
    if(!ui || !ui->core || session.slot>=EP7P_UI_SLOTS || !session.generation) return NULL;
    slot=&ui->slots[session.slot];
    return slot->active && slot->generation==session.generation ? slot : NULL;
}
void ep7p_ui_init(ep7p_ui *ui,ep7p *core) {
    if(ui) { memset(ui,0,sizeof(*ui)); ui->core=core; }
}
static int open_ui(void *opaque,struct ep7_ui_session session,uint16_t mode,uint8_t category) {
    ep7p_ui *ui=opaque; ep7p_ui_slot *slot;
    if(!ui || !ui->core || session.slot>=EP7P_UI_SLOTS || !session.generation || !supported(mode,category)) return EP7_UI_REJECTED;
    slot=&ui->slots[session.slot];
    /* Monotonic per-slot generation: wrap/reuse requires a new boot lifetime. */
    if(slot->active || session.generation<=slot->generation) return EP7_UI_REJECTED;
    *slot=(ep7p_ui_slot){session.generation,true,true,false,mode,category,0};
    return EP7_UI_CHANGED;
}
static int sync_ui(void *opaque,struct ep7_ui_session session,uint16_t mode,uint8_t category) {
    ep7p_ui_slot *slot=lookup(opaque,session); bool changed;
    if(!slot) return EP7_UI_REJECTED;
    changed=slot->mode!=mode || slot->category!=category || !slot->enabled;
    slot->mode=mode; slot->category=category; slot->enabled=supported(mode,category);
    /* Unsupported mode disables editing but does not erase settings/snapshots.
       A later valid sync can re-enable this still-owned UI session. */
    if(!slot->enabled) return EP7_UI_REJECTED;
    return changed ? EP7_UI_CHANGED : EP7_UI_UNCHANGED;
}
static int frame_ui(void *opaque,struct ep7_ui_session session,struct ep7_ui_frame *out) {
    ep7p_ui *ui=opaque; ep7p_ui_slot *slot=lookup(ui,session); int8_t values[12]; unsigned i;
    if(!slot || !slot->enabled || !out || !ep7p_axis_read(ui->core,(unsigned)profile(slot->mode),slot->category-4,values)) return EP7_UI_REJECTED;
    out->public_mode=slot->mode; out->category=slot->category; out->selected_sector=slot->all ? 255 : slot->sector;
    for(i=0;i<12;i++) out->logical_steps[i]=values[i];
    return EP7_UI_UNCHANGED;
}
static int event_ui(void *opaque,struct ep7_ui_session session,enum ep7_ui_event event,uint16_t repeat) {
    ep7p_ui *ui=opaque; ep7p_ui_slot *slot=lookup(ui,session); int delta; unsigned axis,sector; bool changed;
    if(!slot || !slot->enabled || !repeat || repeat>64) return EP7_UI_REJECTED;
    switch(event) {
    case EP7_UI_SECTOR_PREVIOUS:
    case EP7_UI_SECTOR_NEXT:
        changed=slot->all || repeat%12!=0;
        slot->all=false;
        slot->sector=(uint8_t)((slot->sector+(event==EP7_UI_SECTOR_NEXT ? repeat%12 : 12-repeat%12))%12);
        return changed ? EP7_UI_CHANGED : EP7_UI_UNCHANGED;
    case EP7_UI_TOGGLE_ALL:
        if(repeat!=1) return EP7_UI_REJECTED;
        slot->all=!slot->all; return EP7_UI_CHANGED;
    case EP7_UI_RESET_CURRENT_AXIS:
        if(repeat!=1) return EP7_UI_REJECTED;
        delta=0; sector=255; break;
    case EP7_UI_VALUE_INCREASE:
    case EP7_UI_VALUE_DECREASE:
        delta=event==EP7_UI_VALUE_INCREASE ? (int)repeat : -(int)repeat;
        sector=slot->all ? 255 : slot->sector; break;
    default:return EP7_UI_REJECTED;
    }
    axis=slot->category-4;
    if(!ep7p_axis_adjust_result(ui->core,(unsigned)profile(slot->mode),axis,sector,delta,
                               event==EP7_UI_RESET_CURRENT_AXIS,&changed)) return EP7_UI_REJECTED;
    return changed ? EP7_UI_CHANGED : EP7_UI_UNCHANGED;
}
static void close_ui(void *opaque,struct ep7_ui_session session) {
    ep7p_ui_slot *slot=lookup(opaque,session);
    if(slot) { slot->active=false; slot->enabled=false; }
}
const struct ep7_ui_adapter_ops ep7p_ui_ops={open_ui,sync_ui,event_ui,frame_ui,close_ui};
