# E-P7 native seam / compile-only forwarders

## What actually exists

Exact stock 1420/1100 SHA256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`; prior SHA-guarded CPU-builder, stage-admission and task-identity probes establish the following locations. No seam has been installed.

1. Capture population finishes sequential S reads at 602a86b7, capture pointer in d3. Native mode/profile/S are not proven atomically coherent. There is NO native H/L snapshot API or generation token established. Proposed `capture_snapshot_acquire` requires an earlier immutable, generation-bound attachment propagated through the audited clone; reading current UI at job construction is expressly not a substitute.
2. Fresh-job call 603e6d3e invokes 603537eb with a0=32-byte input header, a1=stack+12 uint16 error output, d0=0. `call [d2,d3,a2,a3],44`; result d0 is stored to descriptor+36 at 603e6d45. The error halfword is checked. A changed allocation must be independently known to have requested/initialized the enlarged size; reading a trailer magic is not admission. Stock allocates 15488 and initializes its existing tail. No unused bytes are claimed.
3. Converter 603e62d1 runs only after constructor error==0. Conversion result is stored to the error slot; 603e6d7c..81 gates process on zero. Proposed immutable attachment can only be published after both capture identity and fresh allocation are qualified. Attachment failure must leave native path usable with stock S and no H/L admission.
4. Process call 603e6d84: a0=descriptor, `call [d2,a2,a3],24`, returns d0 status. This identifies outer invocation ownership, not a valid time to decode an as-yet uninitialized embedded request. The direct lifecycle prototype registers only the fresh allocation here, calls stock processing even when admission fails, and preserves d0 status. Existing 603e6d89 stores the process result to error slot.
5. Common cleanup 603e6d8d is reached from constructor/converter/process error paths. a0=descriptor, `call [a2,a3],24`. Proposed admission invalidation must precede this call, including partial-construction failure; any scoped alternative must leave exact-token/LIFO, while the direct path uses allocation revocation without a task scope. Task termination, exceptions/nonlocal exits are NOT covered merely by this normal CFG.
6. Conditional native stage index2 function6036884d reaches embedded request+11364 through60366f21. Supported reader must reject external requests, alternate stage headers, type3 rebuilds, wrong owner/mode, unregistered allocation or invalid lifetime; a scoped alternative additionally checks its exact scope. Type0 builder603397db conditionally calls603aaced→603b17e6/603b1819→603b1466→603b0252→603b0068 synchronously before603450dd installation. All these guards remain necessary; normal100d alone is not sufficient.

## Register, MDR, flags and stack policy

`native_forwarders.s` contains only four SELF-AUTHORED unresolved tail JMPs. They preserve entry state by not introducing a frame, arithmetic, register moves or portable callbacks, then delegate entirely to the named native target. They must be invoked with the listed NATIVE `call [saved-register-list],frame-size` tuple; they are **not ordinary C-callable functions**, and cannot be called with a generic `call [],4` except where separately qualified. The constructor/process/cleanup native frame sizes differ. Linking or placing these thunks is out of scope.

The downstream native functions are allowed their observed ABI clobbers. No guarantee is made that d0/d1/a0/a1, MDR, PSW, loop registers, extended registers or other live state survive them; constructor/process have meaningful return d0. `get_tid` requires `call [a2],4`, a0=aligned writable uint16 output, returns status d0; on failure the output is not valid. It is not a task-generation API.

An arbitrary mid-function observer is not supplied. The new **exact-call-site**
[post-builder bridge](../../prototypes/ep7_volatile_hl/target/postbuilder/) is narrower:
it delegates to the original builder with its native96-byte frame, preserves the
post-builder volatile registers/MDR, passes restored setup a2 as GCC argument d0,
and returns through the original native frame. Exact continuation establishes a
fresh condition before use, so fullPSW writes are neither needed nor introduced.
Current compiler objects are checked to avoid hardware-loop/extended-register
instructions. Unknown helper ABI/control-state effects remain unqualified.

Verified-source MN10300 GCC13.4 now compiles actual core/UI/decoder/lifecycle and
memory code, plus the32-bit-only native setup observer. GCC d0/d1 arguments remain
different from native a0/a1 conventions; generic casts are invalid. The observer
reads setup request/output pointers only under native-readable-buffer/lifetime
preconditions and calls the direct live-allocation reader. This is real unlinked
source integration, not silicon validation, safe placement or an installed hook.

No native lock/TLS facility, scoped context store, task-reuse handling, capture snapshot attachment, constructor enlargement or error-unwind adapter is implemented by these files. Header callbacks are a host vocabulary and MUST remain unbound on target until implemented and verified. No raw last-job global is acceptable.

## Exact output record map (not calibrated H/L behavior)

At603b02c5 selector loads `B=*(setup+12)` into d1 for603b0068. Builder sets output record start to B+688 (603b006e), creates six word destinations +0/+4/+8/+12/+16/+20, and advances each by24. Two outer passes p=0,1 each contain six iterations k=0..5. Input S index is2*k+p (603b00e4..e9); output j=6*p+k. Source record is tablebase0x6051de2c+168*p+28*k.

Source halfword+12 goes into output record+18 (603b015b shift16,603b016a storewordat+16). Source halfword+16 goes into output record+22 (603b016b shift16,603b017a storewordat+20). Calculated S occupies output record+20 lowhalfword, so wholeword writes would destroy S. Candidate H/L lane offsets are therefore **706+24*j and710+24*j**, each2bytes, mapped from input bin2*k+p. Last write ends at B+976 exclusive; B+976 itself is a separate stock write603b01d8. This is independent E-P7 layout evidence, not PEN-F0x2b6 transplant. Hue/lightness interpretation remains comparative; LUT calibration/pixel effects and target post-build placement are not proven. Host demonstration may modify a bounded byte buffer only, preserving every other byte, not dereference native B.

## Local build provenance

Verified GNU2.45 source archive SHA256 `c50c0e7f9cb188980e2cc97e4537626b1672441815587f1eab69d2a1bfbef5d2`, original source metadata `toolchains/binutils-2.45-provenance.json`. Existing original build disabled gas. Separate `toolchains/binutils-2.45-gas-build` configured target mn10300-elf, disabled nls/werror/gdb/gdbserver/sim/ld/gprof/gprofng/gold/libctf/shared, then `make -j4 all-gas MAKEINFO=true`. No system install. as-new SHA256 `5833fa140051525c4d432be6a931abc32e6b866f2a7152f16c1751a5f3122d6c`.

`check_native_forwarders.py` assembles the four thunks, verifies exactly four JMP instructions in a 20-byte text section, four PCREL32 unresolved relocations and no native addresses/resolved linkage, and compile-checks the host header. Object is ignored local scratch, never a firmware image or executable. No vendor bytes are in the self-authored source/object. No firmware or shim was executed.

The output-layout audit is [`tools/ep7_output_layout.py`](../../tools/ep7_output_layout.py);
its [report](../../research/ep7/output-layout-1100.json) includes 31 instruction
witnesses, both destination-pointer strides, and the host buffer bounds.
The prototype headers/forwarders live in
[`prototypes/ep7_volatile_hl`](../../prototypes/ep7_volatile_hl/).

## Current initialization-order constraint

The proposed outer process boundary in item4 identifies invocation ownership,
but is **not** itself a valid time to decode/enter an embedded-request reader
scope: request/operation fields are populated later inside processing. The
portable bounded decoder now validates a real, stable job byte buffer only after
initialization, including current stage index2 and the selected operation’s backlinks after
membership among16 slots.
An eventual adapter must carry the fresh-job capability through the outer
invocation. At the actual synchronous CPU builder observation it can use the
direct live-allocation reader, or a separately qualified narrow scoped reader. It must invalidate before native cleanup; failure to acquire
the lock for revocation cannot be treated as successful cleanup permission.
No native context propagation or failure quarantine is installed by this note.

## Direct lifecycle and capture attachment continuation

The [direct/lifecycle C integration](../../prototypes/ep7_volatile_hl/DIRECT_LIFECYCLE.md)
requires no current-task query. It validates registered allocation membership
before decoding, copies H/L under the revocation lock, and applies only local
values to native-owned output. This does not detect replay across address reuse;
the exact synchronous native lifetime must exclude that ABA case. Failed
invalidation quarantines the host demonstration allocation rather than freeing it.
Native quarantine and lock adapters are not installed.

The [capture attachment evidence](CAPTURE_ATTACHMENT.md) now joins a fresh
registry allocation to population and identifies retirement-before-pool-release.
Node publication occurs before population, and node destruction is not always
capture retirement. Generation-bound unsealed/sealed transfer and clone bracketing
are therefore necessary; merely reading current settings at job construction or
copying a sidecar after native memcpy is insufficient. The normal return from
population is not a Boolean success status.
