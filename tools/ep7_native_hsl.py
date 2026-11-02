"""Build1100 same-wheel PEN-F adapter installation preimages; no hashes.

Get/default: property service60acb0dc slots8/152, native CALLS full entries.
Set:607fa355 inner manager CALL e0/16; return through608274b3 notifications.
Wheel:609330f9 single12-value loop over table60b40c4c; cursor read unchanged.
Dispatch: common FSM body after register saves; native four-category lifecycle.
Paint: container slot160 (NOT leaf widget slot568), full original60d02f93.
Updates: two request278 native refresh calls; preserve their stock resumes.
"""
CALLS = [
    (0x607fa355,'ep7h_set_bridge',0x60827440,0xe0,16),
    (0x609330f9,'ep7h_wheel_bridge',0x602afa81,0,4),
]
POINTERS = [
    (0x60acb0e4,'ep7h_get_bridge',0x607f9549),
    (0x60acb174,'ep7h_default_bridge',0x607f964a),
    (0x61032fb0,'ep7h_paint',0x60d02f93),
]
JUMPS = [
    (0x60d1145e,'ep7h_dispatch_bridge','cd64010000'),
    (0x60d7ad2a,'ep7h_initial_bridge','cdf9002008'),
    (0x60d7adb4,'ep7h_changed_bridge','cd6f002008'),
]
