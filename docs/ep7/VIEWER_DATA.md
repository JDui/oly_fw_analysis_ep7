# COLOR viewer: selected S value, icon maps and native display transport

## Result

The reviewed COLOR viewer is not a caller-owned12-value/range drawing API. Its data-source half is tightly coupled to stock S property IDs and stock cursor/ALL properties. A small reusable **pure lookup** helper exists, but is not a renderer. The bounded path below provides concrete integration constraints; it does not establish absence of every reusable drawing primitive elsewhere.

## Source and output path

Viewer factory84 creates408-byte object; draw60e26ab0 clears334 bytes atobject+4 and44 bytes atobject+340. It refreshes native category/property111. Existing category switch covers0..3 only; category1 COLOR calls60e27289 (`CALL[d2,d3,a2,a3],44`, a0/a1 both viewer in observedcaller60e26ba1).

COLOR sets descriptor+0 (viewer+340) to6. It reads mode atviewer+400, then cursor IDs1091/1096/1097/1686 for public modes54/55/56/64. Cursor255 meansALL, with auxiliary ALL-state properties1098/1099/1100/1687 (this getter route tests zero/nonzero; it does not establish their full semantics). Otherwise(cursor-1)*2 selects ONE property ID from12-halfword table:

| public profile | table | selected S IDs |
|---|---|---|
|54|611899b8|927..938|
|55|611899d0|939..950|
|56|611899e8|951..962|
|64|61189a00|1655..1666|

60e27419..27423 calls property object virtual+8 to read the selected scalar into localsp+24. It does not accept an external axis array. The reviewed data getter path does not require an S setter, but calling this original viewer unchanged will still read S rather than H/L.

The selected cursor/value is converted to display bytes in the cleared334-byte region. Cursor map61189a18 has13 rows(0..12). Value sign map61189a80 and magnitude map61189ad8 each have11 rows for **-5..+5 only**. The sign outputs are3/1/2 fornegative/zero/positive; magnitude output abs(value)+1. There are no entries for-7,-6,+6,+7. Do not silently clamp H/L to fit S graphics or claim these tables qualify the portable±7 design.

At60e26bcf helper60ea4c1c copies11 words(44bytes) toglobal62473fe8. At60e26be3 helper60cfeca9 publishes displayproperty229,334bytes fromviewer+4. The downstream consumer60d7adbb retrieves44bytes with60ea4c2e and sends them toFFE4 displayservice through60ea250b. This is native global/service transport, not a pure draw function whose parameter is12 caller-owned values. Display lifetime, ownership and rendering context remain native obligations.

## Exact small helper interface: usable table lookup, NOT draw

60df24f1 is called with `CALL[d2,d3],8`. Inputs: d0=32-bitkey; d1=unsignedrowcount; a1=table of8-byte rows(key32,value32); callerstack+4 contains writable1-byte outputpointer (callee loads it atsp+12). Input a0 is unused before being replaced by that outputpointer. Caller must provide aligned readable rows and valid writable byte. It searches rows; on equality writes low8bits of row.value; onzero count/no match does NOT write the output. No calls, property access or globals occur in this26-byte body. d2/d3 are restored by RETF[d2,d3],8; d0/a0/a1/flags and loop state may change (the helper executes SETLB/LCS). Return d0 is not a reliable found/not-found status; observed callers use the outputbyte.

A new private15-row map could mechanically include-7..+7, but existing icon/resource meanings beyondthese6magnitude choices are NOT qualified. Reusing this lookup does not supply glyphs, axis labels or a12-bandgraph. It is not GCC-C ABI and no executable bridge to it is supplied.

## Minimal H/L viewer obligations, avoiding stock S setters

1. Extend category4/5 controller/parent factory selection and viewer branch together; the current parent and viewer both stopat0..3. Merely exposing categories or returningnative1 will not render them.
2. Use a copied portable `ep7_ui_frame` (axis,mode,sector/ALL,12values,limits) as sole H/L data source; never substitute S property IDs. Session/parent generation must stay valid and UI execution serialized through rendering.
3. Implement selected-value/ALL presentation and explicitH/L label. The current native view does not consume a caller12-value array; a minimal initial viewer can show the active sector/value without claiming a new12-bandgraph. If graph drawing is required, qualify a separate graphics helper/resource interface first.
4. Provide correct±7 display assets or text formatting, includingnegative signs and±6/±7. Stock±5 iconmaps are insufficient. Keep native S presentation unchanged in categories0..3.
5. Own correctly sized display records/resources, publish under the native drawing-context/lifetime contract, and rebuild/dispose them oncategory/profile/exit transitions. Do not borrow unexplained objectpadding or reuse stale native pointer fields.
6. Gate `renderer_ready` false until these nativebindings and resource semantics are implemented/reviewed. The compile-only event bridge only requests viewer virtual0; it does not fulfill any of them.

Reproduction: `tools/ep7_viewer_data.py`, `tests/test_ep7_viewer_data.py`, and `research/ep7/viewer-data-1100.json`. Exact-stock SHA guard,171 instruction witnesses/9windows,4S-ID tables and3iconmaps;8tests pass. No native drawing execution, S setter, firmware modification or install.
