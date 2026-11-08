.text
.global ep7dr_version_body_bridge
ep7dr_version_body_bridge:
 /* Two BODY current-version text setters, outside the 8-byte wire fields.
  * Preserve unavailable/error text and every lens/accessory version. */
 movhu (a1),d0
 cmp 49,d0
 bne .Lstock_version
 movhu (2,a1),d0
 cmp 46,d0
 bne .Lstock_version
 movhu (4,a1),d0
 cmp 49,d0
 bne .Lstock_version
 movhu (6,a1),d0
 cmp 0,d0
 bne .Lstock_version
 mov _ep7hl_version_text,a1
.Lstock_version:
 jmp ep7dr_stock_version_set_text_unresolved
