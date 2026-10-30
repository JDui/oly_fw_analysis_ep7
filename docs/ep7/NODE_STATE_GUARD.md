# Narrow supported-state guard, exact bridge boundaries

Policy proposal only: initialize registry empty at controller init; before every actual state commit with oldstate33 (including33→33) revoke admissions. Entering33 creates a new supported-context generation; old nodes cannot revive merely by pointer/tag when state33 returns. Merely requesting a state through89c18 is not a commit. Deferred callbacks may dispose nodes before commit, so this guard does NOT replace within33 node-free coverage.

Helper entry60289c5e is called from loop8996f,89aa4,89bdc with saved[d2,d3,a2],frame16; returns89d15 via RET same mask/frame. It has no standalone prologue to reinterpret as a fresh C ABI. The native deferredservice calls are60289c5e and60289d02, both call6028a882,[d2,d3,a2,a3],32.

A possible exact whole-instruction call replacement must cover **both servicecalls**, not just helper entry. Original helper can runnewentry at89cfa thenservice at89d02 and jump directly89c79, bypassing initial89c5e. A wrapper would execute originalservice once, then an observer, then return respecting the original call ABI. It must not observe before originalservice, which may schedule another state or dispose nodes.

After first service:89c63 reads pending,89c69 clearsd2,89c6a setsd3=255,89c6d/e tests pending; sentinel path exits, otherwise89c73 setsa2ROMbase then89c79/7f readold/new. After second service:89d07 readspending,89d0d/e tests255,89d10→89c79. Neither path contains an intervening function call or native state write between postservice observation and old/new commit loads. This is only a same-controller sequential contract, not exclusion of interrupts, foreignthreads or indirectstatewriters. Wrapping both calls requires independent frame/return and registry synchronization qualification; no assembler/installbytes supplied.

Alternative precommit boundary is89c85 before six-byte native MOVHU storingpreviousstate. Live values at boundary are d2=oldstate,d0=newstate,a2=ROMtable6042d570,d3=255. These native values must survive observer. Incoming condition codes are not live to a later branch: native89c9d AND and89ca0 CMP precede first branch89ca2. Therefore do not demand blanket PSW restoration (especially interruptmask restoration) as an invented requirement. There is no explicit incomingMDR consumer in this local continuation before calls/RET; this negative local observation is not a general cross-call ABI guarantee. Do not blanket-save opaque status/control registers without evidence.

Direct literal inventory:21 exact references to currentstate62234fc0; two classified absolute MOVHU stores897d7(init) and89c8b(commit),19 directloads. Pinning these observations does not rule out computedpointer stores, startupbulkclear, anothercore or futurefirmware. An installable guard still needs the explicit local controller/task contract.

The probe checks the exact decoded-main SHA and 36 instruction witnesses, records the explicitly supplied trusted objdump hash, and verifies 21 literal-reference offsets using the same verified temporary bytes. It never executes MN103 code.

## Deferredservice nested-call ABI scope

Full service window8a882..8a92b (170bytes) has direct SP slots+4,+8,+12 only, all initialized locally before reads:883→+4,899→+8,89b→+12. Its return8a929 is RET[d2,d3,a2,a3],32. Direct service body therefore supplies no evidence of caller stack arguments needing forwarding; nested invocation with native frame32 recreates the documented locals. It invokes registered callbacks viaCALLS and helper8a92c via nativeCALL; this is not a proof of arbitrary callbacks avoiding caller-stack introspection. Supported callback set/context contract remains explicit.

First postservice branch flags are produced by nativeCMP89c6d on initial path andCMP89d0d on loop path, respectively. No fullPSW restore needed solely to preserve the prior service flags. Both service and enclosinghelper use RET, not RETF; no explicit incomingMDR read occurs in these reviewed bodies, but any bridge should follow tested nativecallreturn rules rather than infer an entire undocumented ABI. No generic status-register restoration is proposed.

Final guardprobe:36 instruction witnesses plus21directliteral references; fullservice hash is recorded. Two tests pass locally (inputguard and actualstockstatic); latter skips on clean checkout withoutfixture/tool.


## Reproduce

Run `python tools/ep7_node_state_guard.py --decoded generated/ep7/main.decoded.bin --objdump toolchains/binutils-2.45-build/binutils/objdump`. The decoded image is a private local input and is not included. `tests/test_ep7_node_state_guard.py` skips its actual-stock integration check when the private input/tool is absent; guard/table tests remain available. No firmware code is executed.
